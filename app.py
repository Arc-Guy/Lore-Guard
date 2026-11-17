
import streamlit as st
import json
from pathlib import Path

from consistency_engine import load_memory, save_memory
from lore_guard import audit_lore
from fact_extractor import extract_candidates
from ai_generator import generate_screenplay


# ==========================================
# 1. CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="LoreGuard AI",
    page_icon="📖",
    layout="wide"
)

MEMORY_FILE = Path(__file__).parent / "memory.json"


# ==========================================
# 2. GENERATION AND INTEGRATION
# ==========================================

from integration import generate_and_check


# ==========================================
# 3. LOAD MEMORY
# ==========================================

if "memory" not in st.session_state:
    st.session_state.memory = load_memory(MEMORY_FILE)

if "screenplay" not in st.session_state:
    st.session_state.screenplay = ""

if "branches" not in st.session_state:
    st.session_state.branches = []

if "report" not in st.session_state:
    st.session_state.report = None

memory = st.session_state.memory


def persist_memory():
    save_memory(st.session_state.memory, MEMORY_FILE)


# ==========================================
# 4. APPLICATION HEADER
# ==========================================

st.title("📖 LoreGuard AI")

st.markdown(
    "### Your intelligent storytelling and screenplay co-writer"
)

st.caption(
    "Maintain character personalities, protect story lore "
    "and explore alternative narratives."
)

st.success("Generation and consistency integration is available.")

st.divider()


# ==========================================
# 5. SIDEBAR
# ==========================================

st.sidebar.title("📖 LOREGUARD")

page = st.sidebar.radio(
    "NAVIGATION",
    [
        "Dashboard",
        "Character Studio",
        "Lore Manager",
        "Screenplay Generator",
        "Consistency Report",
        "Story Branches"
    ]
)

st.sidebar.divider()

st.sidebar.caption("STORYTELLING WORKSPACE")


# ==========================================
# 6. DASHBOARD
# ==========================================

if page == "Dashboard":

    st.header("Welcome to LoreGuard")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Characters",
        len(memory.get("characters", {}))
    )

    col2.metric(
        "Established Facts",
        len(memory.get("established_facts", []))
    )

    col3.metric(
        "Story Branches",
        len(st.session_state.branches)
    )

    st.divider()

    st.subheader("Your Story Universe")

    st.write(
        "Manage your fictional universe and keep "
        "every generated scene consistent."
    )

    st.subheader("Characters")

    characters = memory.get("characters", {})

    if characters:

        for name, profile in characters.items():

            with st.expander(name):

                st.write(
                    profile.get("description", "No description")
                )

                st.write(
                    "Traits:",
                    ", ".join(profile.get("traits", []))
                )

    else:
        st.info("No characters created yet.")

    st.subheader("World Rules")

    for rule in memory.get("world_rules", []):

        st.write(
            f"• {rule.get('description', rule.get('id', 'Rule'))}"
        )


# ==========================================
# 7. CHARACTER STUDIO
# ==========================================

elif page == "Character Studio":

    st.header("👥 Character Studio")

    st.write(
        "Create and edit the personalities of your characters."
    )

    characters = memory.setdefault("characters", {})

    for name, profile in list(characters.items()):

        with st.expander(f"Character: {name}"):

            with st.form(f"edit_{name}"):

                description = st.text_area(
                    "Description",
                    value=profile.get("description", "")
                )

                traits = st.text_input(
                    "Personality traits (comma separated)",
                    value=", ".join(profile.get("traits", []))
                )

                facts_json = st.text_area(
                    "Known facts (JSON)",
                    value=json.dumps(
                        profile.get("known_facts", {}),
                        indent=2
                    )
                )

                save = st.form_submit_button("Save Character")

                if save:

                    try:

                        known_facts = json.loads(facts_json)

                        if not isinstance(known_facts, dict):
                            raise ValueError(
                                "Known facts must be a JSON object."
                            )

                        profile["description"] = description

                        profile["traits"] = [
                            t.strip()
                            for t in traits.split(",")
                            if t.strip()
                        ]

                        profile["known_facts"] = known_facts

                        persist_memory()

                        st.success("Character updated!")
                        st.rerun()

                    except (ValueError, json.JSONDecodeError) as e:

                        st.error(f"Invalid character data: {e}")

    st.divider()

    st.subheader("Create a New Character")

    with st.form("new_character"):

        new_name = st.text_input("Character Name")

        new_description = st.text_area(
            "Character Description"
        )

        new_traits = st.text_input(
            "Personality Traits",
            placeholder="Brave, loyal, intelligent"
        )

        create = st.form_submit_button("Add Character")

        if create:

            if not new_name.strip():

                st.warning("Enter a character name.")

            elif new_name.strip() in characters:

                st.warning("This character already exists.")

            else:

                characters[new_name.strip()] = {
                    "description": new_description,
                    "traits": [
                        t.strip()
                        for t in new_traits.split(",")
                        if t.strip()
                    ],
                    "contradictory_traits": {},
                    "known_facts": {}
                }

                persist_memory()

                st.success("New character created!")
                st.rerun()


# ==========================================
# 8. LORE MANAGER
# ==========================================

elif page == "Lore Manager":

    st.header("📚 Lore Manager")

    st.write(
        "Manage established facts and world rules."
    )

    st.subheader("Established Facts")

    facts = memory.setdefault("established_facts", [])

    for fact in facts:

        st.write(
            f"**{fact.get('subject')}** — "
            f"{fact.get('predicate')}: "
            f"{fact.get('value')}"
        )

    st.divider()

    st.subheader("Add an Established Fact")

    with st.form("add_fact"):

        subject = st.text_input("Character / Subject")

        predicate = st.text_input(
            "Fact category",
            placeholder="knows_language"
        )

        value = st.text_input(
            "Established value",
            placeholder="French"
        )

        add = st.form_submit_button("Save Fact")

        if add:

            if subject.strip() and predicate.strip() and value.strip():

                new_fact = {
                    "id": f"F-{len(facts) + 1:03d}",
                    "subject": subject.strip(),
                    "predicate": predicate.strip(),
                    "value": value.strip(),
                    "severity": "high"
                }

                facts.append(new_fact)

                persist_memory()

                st.success("Fact saved!")
                st.rerun()

            else:

                st.warning("Complete all three fields.")

    st.divider()

    st.subheader("World Rules")

    for rule in memory.get("world_rules", []):

        st.info(rule.get("description", "Unnamed world rule"))

    st.caption(
        "World rules and established facts are stored "
        "in memory.json."
    )


# ==========================================
# 9. SCREENPLAY GENERATOR
# ==========================================

elif page == "Screenplay Generator":

    st.header("✍️ Screenplay Generator")

    prompt = st.text_area(
        "Describe the scene you want to create",
        placeholder=(
            "Example: Mira discovers a hidden letter "
            "and confronts the person who betrayed her."
        ),
        height=130
    )

    genre = st.selectbox(
        "Choose a genre",
        [
            "Mystery",
            "Drama",
            "Thriller",
            "Fantasy",
            "Science Fiction"
        ]
    )

    if st.button("Generate Screenplay", type="primary"):

        if not prompt.strip():

            st.warning("Enter a scene description.")

        else:
            with st.spinner("Generating screenplay..."):
                result = generate_and_check(
                    generate_screenplay,
                    {
                        "prompt": prompt,
                        "genre": genre,
                        "memory": memory,
                        "characters": memory.get("characters", {}),
                        "branch_count": 3,
                    },
                    memory,
                    branches=True,
                )

            if not result["ok"]:
                st.error(result["error"])
            else:
                branch_results = result["results"]
                st.session_state.branches = branch_results
                st.session_state.report = (
                    branch_results[0]["report"] if branch_results else None
                )
                st.session_state.screenplay = "\n\n".join(
                    item["branch"].get("screenplay_text", "")
                    for item in st.session_state.branches
                    if item["branch"].get("screenplay_text")
                )
                st.success("Generation completed and all branches were checked.")

    st.divider()

    st.subheader("Screenplay Editor")

    screenplay = st.text_area(
        "Enter or paste screenplay text",
        value=st.session_state.screenplay,
        height=250,
        placeholder="Paste your screenplay here..."
    )

    if screenplay != st.session_state.screenplay:
        st.session_state.screenplay = screenplay
        st.session_state.report = None

    if st.button("Check Screenplay Consistency"):

        if not screenplay.strip():

            st.warning("Enter screenplay text first.")

        else:

            with st.spinner("Checking story lore..."):

                st.session_state.report = audit_lore(
                    memory,
                    screenplay,
                    memory.get("characters", {})
                )

            st.success("Consistency analysis completed!")

    if st.session_state.screenplay:

        st.download_button(
            "Download Screenplay",
            data=st.session_state.screenplay,
            file_name="loreguard_screenplay.txt",
            mime="text/plain"
        )


# ==========================================
# 10. CONSISTENCY REPORT
# ==========================================

elif page == "Consistency Report":

    st.header("🔍 Consistency Report")

    report = st.session_state.report

    if report:

        score = report.get(
            "score",
            report.get("consistency_score", 0)
        )

        col1, col2 = st.columns(2)

        col1.metric("Consistency Score", f"{score}/100")

        col2.metric(
            "Contradictions",
            len(report.get("issues", []))
        )

        st.progress(score / 100)

        st.subheader("Analysis Summary")

        st.write(report.get("summary", ""))

        st.subheader("Detected Issues")

        issues = report.get("issues", [])

        if issues:

            for issue in issues:

                st.error(
                    f"{issue.get('severity', 'Unknown')}: "
                    f"{issue.get('description', 'Issue detected')}"
                )

        else:

            st.success(
                "No contradictions detected among the facts "
                "recognized by the current checker."
            )

        st.divider()

        st.subheader("Extracted Story Facts")

        extracted = extract_candidates(
            st.session_state.screenplay
        )

        for fact in extracted["candidate_facts"]:

            st.write(
                f"• {fact['subject']} — "
                f"{fact['predicate']}: {fact['value']}"
            )

        st.caption(
            f"{len(extracted['ignored_sentences'])} sentence(s) "
            "could not be interpreted by the current extractor."
        )

    else:

        st.info(
            "Generate or paste a screenplay and run "
            "the consistency checker to view a report."
        )


# ==========================================
# 11. STORY BRANCHES
# ==========================================

elif page == "Story Branches":

    st.header("🌳 Alternative Story Branches")

    st.write(
        "Explore alternative directions for your narrative."
    )

    if st.session_state.branches:

        for i, branch_result in enumerate(
            st.session_state.branches
        ):
            branch = branch_result.get("branch", {})
            report = branch_result.get("report", {})
            score = report.get(
                "score",
                report.get("consistency_score", 0)
            )

            with st.expander(f"Story Branch {i + 1}"):

                st.subheader(branch.get("title", f"Branch {i + 1}"))

                col1, col2 = st.columns(2)
                col1.metric("Consistency Score", f"{score}/100")
                col2.metric("Contradictions", len(report.get("issues", [])))

                if report.get("consistent", not report.get("issues")):
                    st.success("This branch is consistent with the story memory.")
                else:
                    st.error("This branch contains continuity problems.")

                if branch.get("screenplay_text"):
                    st.markdown(branch["screenplay_text"])

                for issue in report.get("issues", []):
                    st.warning(issue.get("message", issue.get("description", "Issue detected")))

                with st.expander("Structured scene data"):
                    st.json(branch)

    else:

        st.info(
            "Alternative branches will appear here "
            "when Person 1's generation engine is connected."
        )


# ==========================================
# 12. FOOTER
# ==========================================

st.sidebar.divider()

st.sidebar.caption("LOREGUARD | AI STORYTELLING")

