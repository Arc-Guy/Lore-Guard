import json
import os

MEMORY_FILE = "story_memory.json"


def load_memory():
    """Load permanent story memory."""

    default_memory = {
        "characters": [],
        "lore": "",
        "chapters": []
    }

    if not os.path.exists(MEMORY_FILE):
        return default_memory

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as file:
            memory = json.load(file)

        # Ensure all required sections exist
        for key, value in default_memory.items():
            if key not in memory:
                memory[key] = value

        return memory

    except (json.JSONDecodeError, OSError):
        return default_memory


def save_memory(memory):
    """Save story memory permanently."""

    with open(MEMORY_FILE, "w", encoding="utf-8") as file:
        json.dump(
            memory,
            file,
            indent=4,
            ensure_ascii=False
        )


def add_character(character):
    """Add a character permanently."""

    memory = load_memory()

    memory["characters"].append(character)

    save_memory(memory)


def update_lore(lore):
    """Update world lore permanently."""

    memory = load_memory()

    memory["lore"] = lore

    save_memory(memory)


def save_chapter(chapter):
    """Save a chapter and its AI analysis permanently."""

    memory = load_memory()

    # Ensure chapters list exists
    if "chapters" not in memory:
        memory["chapters"] = []

    # Add the new chapter
    memory["chapters"].append(chapter)

    # Save everything to JSON
    save_memory(memory)

    return True


def get_chapters():
    """Retrieve all saved chapters."""

    memory = load_memory()

    return memory.get("chapters", [])
