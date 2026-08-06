"""Local keys and the party-held record.

Two things are held. Signing keys live in memory for the life of the process
and are never written to disk, never returned by a tool, and never placed in
a log line or an error message. Public keys and shared objects are held in
memory too, and are additionally written to a state directory when the caller
names one, so that a record survives a restart and stays verifiable by a
counterparty that holds only the public half.

Losing the private half on restart is the deliberate consequence. A process
that has forgotten a key can no longer sign under it, which is a smaller
failure than a demonstration surface that writes private keys to a directory
somebody will later copy.
"""

from __future__ import annotations

import json
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from a202_reference.signing import generate_key, public_key_of


class KeyUnavailable(Exception):
    """A key exists in the record but its private half is not in this process."""


class KeyMisbound(Exception):
    """A key was presented as belonging to a party element that does not own it."""


class LocalState:
    """The objects, events, keys, and key bindings this process holds.

    One process holds every key it is asked to sign with, which is what lets a
    single server demonstrate both sides of a bilateral exchange from one
    machine. It is not two parties, and nothing here establishes that two
    organisations independently held the keys they signed with. A deployment
    where each organisation runs its own instance gets that property from the
    deployment; this class does not provide it and does not claim to.

    What it does hold is the binding between a key identifier and the party
    element that owns it, so that a key registered to an agent cannot later
    sign as a principal.
    """

    def __init__(self, state_dir: str | Path | None = None) -> None:
        self.state_dir = Path(state_dir) if state_dir else None
        self._private: dict[str, object] = {}
        self._public: dict[str, object] = {}
        self._objects: dict[str, dict] = {}
        self._mandates: dict[str, dict] = {}
        self._principal_keys: dict[str, str] = {}
        self._agent_key_owners: dict[str, str] = {}
        self._agent_keys: dict[str, set] = {}
        if self.state_dir is not None:
            (self.state_dir / "objects").mkdir(parents=True, exist_ok=True)
            (self.state_dir / "mandates").mkdir(parents=True, exist_ok=True)
            (self.state_dir / "keys").mkdir(parents=True, exist_ok=True)
            self._load()

    # --- keys ---------------------------------------------------------------

    def signing_key(self, key_id: str):
        """The private key for key_id, generated on first use.

        A key identifier already known from a previous run, whose private half
        this process does not hold, raises rather than silently minting a
        second key under the same identifier: two keys under one identifier
        would make every earlier signature unverifiable against the later one.
        """
        if key_id in self._private:
            return self._private[key_id]
        if key_id in self._public:
            raise KeyUnavailable(
                f"{key_id} was created before this process started; its private "
                "half is held in memory only and is not recoverable"
            )
        key = generate_key()
        self._private[key_id] = key
        self._public[key_id] = public_key_of(key)
        self._write_public(key_id)
        return key

    def public_keys(self) -> dict:
        """Every public key this party holds, in the shape verify_bundle reads."""
        return dict(self._public)

    def known_key_ids(self) -> list[str]:
        return sorted(self._public)

    def bind_principal_key(self, principal_id: str, key_id: str) -> None:
        """Record that key_id is the signing key of principal_id.

        A key belongs to one party element. A second principal claiming a key
        already bound to another, or a key that belongs to an agent, is
        refused: an approval whose key is the acting agent's is the agent
        approving itself, which is the one thing the approval exists to
        prevent.
        """
        bound = self._principal_keys.get(key_id)
        if bound is not None and bound != principal_id:
            raise KeyMisbound(f"{key_id} is already the signing key of {bound}")
        owner = self._agent_key_owners.get(key_id)
        if owner is not None:
            raise KeyMisbound(f"{key_id} is the signing key of agent {owner}")
        for keys in self._agent_keys.values():
            if key_id in keys:
                raise KeyMisbound(f"{key_id} has already signed an act as an agent")
        self._principal_keys[key_id] = principal_id
        self._write_bindings()

    def bind_agent_key(self, agent_id: str, key_id: str) -> None:
        """Record that key_id is the signing key of an agent.

        The binding is learned from the mandate that names the agent and its
        key, which is where a key first becomes an agent's key.
        """
        bound = self._agent_key_owners.get(key_id)
        if bound is not None and bound != agent_id:
            raise KeyMisbound(f"{key_id} is already the signing key of {bound}")
        principal = self._principal_keys.get(key_id)
        if principal is not None:
            raise KeyMisbound(f"{key_id} is the signing key of principal {principal}")
        self._agent_key_owners[key_id] = agent_id
        self._write_bindings()

    def agent_for_key(self, key_id) -> str | None:
        if not isinstance(key_id, str):
            return None
        return self._agent_key_owners.get(key_id)

    def principal_for_key(self, key_id) -> str | None:
        """The principal a key is bound to, or None where it is bound to none."""
        if not isinstance(key_id, str):
            return None
        return self._principal_keys.get(key_id)

    def key_for_principal(self, principal_id) -> str | None:
        """The key bound to a principal, or None where none is."""
        if not isinstance(principal_id, str):
            return None
        for key_id, bound in self._principal_keys.items():
            if bound == principal_id:
                return key_id
        return None

    def record_agent_key(self, transaction_id: str, key_id: str) -> None:
        """Note that a key signed an act as an agent on this transaction."""
        self._agent_keys.setdefault(transaction_id, set()).add(key_id)

    def agent_keys(self, transaction_id: str) -> set:
        return set(self._agent_keys.get(transaction_id, ()))

    # --- objects ------------------------------------------------------------

    def put_object(self, obj: dict) -> None:
        self._objects[obj["id"]] = obj
        if self.state_dir is not None:
            path = self.state_dir / "objects" / f"{obj['id']}.json"
            path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")

    def get_object(self, object_id) -> dict | None:
        """The object held under an identifier, or None.

        A lookup key that is not a string resolves to nothing rather than
        raising: an identifier arrives from a counterparty or a model and is
        not trusted to be of any particular type.
        """
        if not isinstance(object_id, str):
            return None
        return self._objects.get(object_id)

    def objects_for(self, transaction_id: str) -> list[dict]:
        return [
            obj for obj in self._objects.values()
            if obj.get("transaction_id") == transaction_id
        ]

    def events_for(self, transaction_id: str) -> list[dict]:
        """The transaction stream's events, in the order the chain states.

        Ordering is by predecessor reference rather than by a counter, because
        there is no ordering service bilaterally. The sequence member is
        carried because the envelope requires it, and it is not what orders
        the record.
        """
        events = [
            obj for obj in self.objects_for(transaction_id)
            if obj.get("object_type") == "transaction_event"
            and obj["payload"].get("stream", {}).get("id") == transaction_id
        ]
        by_previous = {
            obj["payload"].get("previous_event_hash"): obj for obj in events
        }
        ordered = []
        cursor = by_previous.get(None)
        while cursor is not None:
            ordered.append(cursor)
            cursor = by_previous.get(cursor["content_hash"])
        # An event the walk did not reach is off the chain from the first
        # event. It is reported rather than dropped, because a record with a
        # break in it is a fact about the record.
        reached = {obj["id"] for obj in ordered}
        ordered.extend(sorted(
            (obj for obj in events if obj["id"] not in reached),
            key=lambda obj: obj["payload"].get("sequence", 0),
        ))
        return ordered

    def last_event(self, transaction_id: str) -> dict | None:
        events = self.events_for(transaction_id)
        return events[-1] if events else None

    # --- mandates -----------------------------------------------------------

    def put_mandate(self, mandate: dict) -> None:
        self._mandates[mandate["id"]] = mandate
        if self.state_dir is not None:
            path = self.state_dir / "mandates" / f"{mandate['id']}.json"
            path.write_text(json.dumps(mandate, indent=2, sort_keys=True) + "\n")

    def get_mandate(self, mandate_id) -> dict | None:
        """The mandate held under an identifier, or None, on the same rule as
        get_object: an identifier of the wrong type resolves to nothing."""
        if not isinstance(mandate_id, str):
            return None
        return self._mandates.get(mandate_id)

    # --- persistence --------------------------------------------------------

    def _write_public(self, key_id: str) -> None:
        if self.state_dir is None:
            return
        pem = self._public[key_id].public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        (self.state_dir / "keys" / f"{key_id}.pub.pem").write_bytes(pem)

    def _write_bindings(self) -> None:
        if self.state_dir is None:
            return
        path = self.state_dir / "keys" / "key-bindings.json"
        path.write_text(
            json.dumps(
                {"principals": self._principal_keys, "agents": self._agent_key_owners},
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

    def _load(self) -> None:
        for path in (self.state_dir / "objects").glob("*.json"):
            obj = json.loads(path.read_text())
            self._objects[obj["id"]] = obj
        for path in (self.state_dir / "mandates").glob("*.json"):
            doc = json.loads(path.read_text())
            self._mandates[doc["id"]] = doc
        for path in (self.state_dir / "keys").glob("*.pub.pem"):
            key_id = path.name[: -len(".pub.pem")]
            self._public[key_id] = serialization.load_pem_public_key(path.read_bytes())
        bindings = self.state_dir / "keys" / "key-bindings.json"
        if bindings.exists():
            held = json.loads(bindings.read_text())
            self._principal_keys = held.get("principals", {})
            self._agent_key_owners = held.get("agents", {})
