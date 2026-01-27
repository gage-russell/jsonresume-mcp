"""Data access layer for JSON Resume experience storage with MCP extensions."""

import json
from pathlib import Path
from typing import Callable, Any
from uuid import uuid4

from resumejson_mcp.lib.experience.models import (
    Resume,
    Work,
    Education,
    Skill,
    Project,
    Basics,
    MCPBullet,
    MCPMajorProject,
)
from resumejson_mcp.lib.storage.models import StoragePaths


class ExperienceStore:
    """Manages reading/writing comprehensive experience data with MCP extensions.
    
    Stores all career experience, skills, education, and projects in a single JSON file.
    This data is used to generate tailored resumes for specific job applications.
    """

    def __init__(self):
        self.storage_paths = StoragePaths()
        self.storage_paths.ensure_paths()

    @property
    def experience_file_path(self) -> Path:
        return self.storage_paths.experience_folder / "experience.json"

    # ========================================================================
    # Core Operations
    # ========================================================================

    def load_experience(self) -> Resume:
        if not self.experience_file_path.exists():
            raise FileNotFoundError(f"Experience file not found at {self.experience_file_path}")
        with open(self.experience_file_path, "r") as f:
            return Resume(**json.load(f))

    def save_experience(self, experience: Resume) -> None:
        with open(self.experience_file_path, "w") as f:
            json.dump(
                experience.model_dump(by_alias=True, exclude_none=True),
                f,
                indent=2,
                ensure_ascii=False,
            )

    def initialize_experience(self, basics: Basics | None = None) -> Resume:
        experience = Resume(basics=basics)
        self.save_experience(experience)
        return experience

    def experience_exists(self) -> bool:
        return self.experience_file_path.exists()

    # ========================================================================
    # Internal Helpers
    # ========================================================================

    @staticmethod
    def _find_by_id(items: list, item_id: str, id_attr: str = 'id') -> tuple[int, Any]:
        for idx, item in enumerate(items):
            if getattr(item, id_attr, None) == item_id:
                return idx, item
        raise ValueError(f"Item with {id_attr} '{item_id}' not found")

    def _find_by_mcp_id(self, items: list, mcp_id: str) -> tuple[int, Any]:
        for idx, item in enumerate(items):
            if item.mcp_details and item.mcp_details.id == mcp_id:
                return idx, item
        raise ValueError(f"Item with mcp-details.id '{mcp_id}' not found")

    def _ensure_mcp_id(self, item: Any) -> None:
        if not item.mcp_details:
            raise ValueError("Item must have mcp_details")
        if not item.mcp_details.id:
            item.mcp_details.id = str(uuid4())

    def _modify_and_save(self, modifier: Callable[[Resume], None]) -> None:
        experience = self.load_experience()
        modifier(experience)
        self.save_experience(experience)

    def _get_mcp_ids(self, items: list) -> set[str]:
        return {i.mcp_details.id for i in items if i.mcp_details}

    # ========================================================================
    # Generic CRUD
    # ========================================================================

    def _get_all(self, collection: str) -> list:
        return getattr(self.load_experience(), collection)

    def _get_by_id(self, collection: str, mcp_id: str) -> Any:
        _, item = self._find_by_mcp_id(self._get_all(collection), mcp_id)
        return item

    def _add(self, collection: str, item: Any) -> Any:
        self._ensure_mcp_id(item)
        
        def modifier(exp: Resume) -> None:
            items = getattr(exp, collection)
            if item.mcp_details.id in self._get_mcp_ids(items):
                raise ValueError(f"Item with id '{item.mcp_details.id}' already exists")
            items.append(item)
        
        self._modify_and_save(modifier)
        return item

    def _add_many(self, collection: str, new_items: list) -> list:
        ids: set[str] = set()
        for item in new_items:
            self._ensure_mcp_id(item)
            if item.mcp_details.id in ids:
                raise ValueError(f"Duplicate id in input: '{item.mcp_details.id}'")
            ids.add(item.mcp_details.id)
        
        def modifier(exp: Resume) -> None:
            items = getattr(exp, collection)
            existing = self._get_mcp_ids(items)
            for item in new_items:
                if item.mcp_details.id in existing:
                    raise ValueError(f"Item with id '{item.mcp_details.id}' already exists")
            items.extend(new_items)
        
        self._modify_and_save(modifier)
        return new_items

    def _update(self, collection: str, mcp_id: str, item: Any) -> Any:
        def modifier(exp: Resume) -> None:
            items = getattr(exp, collection)
            idx, _ = self._find_by_mcp_id(items, mcp_id)
            if item.mcp_details:
                item.mcp_details.id = mcp_id
            items[idx] = item
        
        self._modify_and_save(modifier)
        return item

    def _delete(self, collection: str, mcp_id: str) -> bool:
        def modifier(exp: Resume) -> None:
            items = getattr(exp, collection)
            idx, _ = self._find_by_mcp_id(items, mcp_id)
            items.pop(idx)
        
        self._modify_and_save(modifier)
        return True

    # ========================================================================
    # Nested CRUD (for bullets, major_projects within work)
    # ========================================================================

    def _get_nested_list(self, exp: Resume, parent_collection: str, parent_id: str, nested_attr: str) -> tuple[int, Any, list]:
        """Returns (parent_idx, parent, nested_list)."""
        parent_items = getattr(exp, parent_collection)
        idx, parent = self._find_by_mcp_id(parent_items, parent_id)
        if not parent.mcp_details:
            raise ValueError("Parent must have mcp_details")
        return idx, parent, getattr(parent.mcp_details, nested_attr)

    def _nested_add(self, parent_collection: str, parent_id: str, nested_attr: str, item: Any) -> Any:
        if not item.id:
            item.id = str(uuid4())
        
        def modifier(exp: Resume) -> None:
            _, _, nested = self._get_nested_list(exp, parent_collection, parent_id, nested_attr)
            if any(x.id == item.id for x in nested):
                raise ValueError(f"Item with id '{item.id}' already exists")
            nested.append(item)
        
        self._modify_and_save(modifier)
        return item

    def _nested_update(self, parent_collection: str, parent_id: str, nested_attr: str, item_id: str, item: Any) -> Any:
        def modifier(exp: Resume) -> None:
            _, _, nested = self._get_nested_list(exp, parent_collection, parent_id, nested_attr)
            idx, _ = self._find_by_id(nested, item_id)
            item.id = item_id
            nested[idx] = item
        
        self._modify_and_save(modifier)
        return item

    def _nested_delete(self, parent_collection: str, parent_id: str, nested_attr: str, item_id: str) -> bool:
        def modifier(exp: Resume) -> None:
            idx, parent, nested = self._get_nested_list(exp, parent_collection, parent_id, nested_attr)
            original = len(nested)
            filtered = [x for x in nested if x.id != item_id]
            if len(filtered) == original:
                raise ValueError(f"Item with id '{item_id}' not found")
            setattr(parent.mcp_details, nested_attr, filtered)
        
        self._modify_and_save(modifier)
        return True

    # ========================================================================
    # Basics
    # ========================================================================

    def get_basics(self) -> Basics | None:
        return self.load_experience().basics

    def set_basics(self, basics: Basics) -> None:
        self._modify_and_save(lambda exp: setattr(exp, 'basics', basics))

    # ========================================================================
    # Work
    # ========================================================================

    def get_all_work(self) -> list[Work]:
        return self._get_all('work')

    def get_work_by_id(self, mcp_id: str) -> Work:
        return self._get_by_id('work', mcp_id)

    def add_work(self, work: Work) -> Work:
        return self._add('work', work)

    def update_work(self, mcp_id: str, work: Work) -> Work:
        return self._update('work', mcp_id, work)

    def delete_work(self, mcp_id: str) -> bool:
        return self._delete('work', mcp_id)

    # Work Bullets
    def add_bullet_to_work(self, work_id: str, bullet: MCPBullet) -> MCPBullet:
        return self._nested_add('work', work_id, 'bullets', bullet)

    def update_bullet_in_work(self, work_id: str, bullet_id: str, bullet: MCPBullet) -> MCPBullet:
        return self._nested_update('work', work_id, 'bullets', bullet_id, bullet)

    def delete_bullet_from_work(self, work_id: str, bullet_id: str) -> bool:
        return self._nested_delete('work', work_id, 'bullets', bullet_id)

    # Work Major Projects
    def add_major_project_to_work(self, work_id: str, project: MCPMajorProject) -> MCPMajorProject:
        return self._nested_add('work', work_id, 'major_projects', project)

    def update_major_project_in_work(self, work_id: str, project_id: str, project: MCPMajorProject) -> MCPMajorProject:
        return self._nested_update('work', work_id, 'major_projects', project_id, project)

    def delete_major_project_from_work(self, work_id: str, project_id: str) -> bool:
        return self._nested_delete('work', work_id, 'major_projects', project_id)

    # ========================================================================
    # Education
    # ========================================================================

    def get_all_education(self) -> list[Education]:
        return self._get_all('education')

    def get_education_by_id(self, mcp_id: str) -> Education:
        return self._get_by_id('education', mcp_id)

    def add_education(self, education: Education) -> Education:
        return self._add('education', education)

    def update_education(self, mcp_id: str, education: Education) -> Education:
        return self._update('education', mcp_id, education)

    def delete_education(self, mcp_id: str) -> bool:
        return self._delete('education', mcp_id)

    # ========================================================================
    # Skills
    # ========================================================================

    def get_all_skills(self) -> list[Skill]:
        return self._get_all('skills')

    def get_skill_by_id(self, mcp_id: str) -> Skill:
        return self._get_by_id('skills', mcp_id)

    def add_skill(self, skill: Skill) -> Skill:
        return self._add('skills', skill)

    def add_skills(self, skills: list[Skill]) -> list[Skill]:
        return self._add_many('skills', skills)

    def update_skill(self, mcp_id: str, skill: Skill) -> Skill:
        return self._update('skills', mcp_id, skill)

    def delete_skill(self, mcp_id: str) -> bool:
        return self._delete('skills', mcp_id)

    # ========================================================================
    # Projects
    # ========================================================================

    def get_all_projects(self) -> list[Project]:
        return self._get_all('projects')

    def get_project_by_id(self, mcp_id: str) -> Project:
        return self._get_by_id('projects', mcp_id)

    def add_project(self, project: Project) -> Project:
        return self._add('projects', project)

    def add_projects(self, projects: list[Project]) -> list[Project]:
        return self._add_many('projects', projects)

    def update_project(self, mcp_id: str, project: Project) -> Project:
        return self._update('projects', mcp_id, project)

    def delete_project(self, mcp_id: str) -> bool:
        return self._delete('projects', mcp_id)
