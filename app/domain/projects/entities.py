from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass
class Project:
    name: str
    id: UUID = field(default_factory=uuid4)
    description: str | None = None
    owner_id: UUID | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def update(self, name: str | None = None, description: str | None = None) -> None:
        if name is None and description is None:
            return

        changed = False
        if name is not None:
            self.name = name
            changed = True
        if description is not None:
            self.description = description
            changed = True

        if changed:
            self.updated_at = datetime.now(timezone.utc)
