from memory import load_memory, save_memory, save_chapter
import streamlit as st
from google import genai
from dotenv import load_dotenv
import os
import json

# Load API key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Page configuration
st.set_page_config(
    page_title="LoreGuard AI",
    page_icon="📖",
    layout="wide"
)

# Load permanent story memory
if "story_memory" not in st.session_state:
    st.session_state.story_memory = load_memory()

memory = st.session_state.story_memory

if "characters" not in st.session_state:
    st.session_state.characters = memory["characters"]

if "lore" not in st.session_state:
    st.session_state.lore = memory["lore"]

# Connect to Gemini
if api_key:
    client = genai.Client(api_key=api_key)
else:
    client = None

# Application heading
st.title("📖 LoreGuard AI")
st.subheader("Your intelligent narrative consistency assistant")

st.write(
    "Build your fictional universe, remember its characters "
    "and detect contradictions in your stories."
)

st.divider()

# Sidebar
st.sidebar.title("📚 Story Memory")

st.sidebar.write(
    f"Characters saved: {len(st.session_state.characters)}"
)

# Character creation
st.header("1. Character Memory")

with st.form("character_form"):
    name = st.text_input("Character name")
    age = st.text_input("Character age")
    personality = st.text_area("Personality and behaviour")
    abilities = st.text_area("Abilities and limitations")
    history = st.text_area("Important history and events")

    save_character = st.form_submit_button("Save Character")

    if save_character:
        if name.strip():
            character = {
                "name": name,
                "age": age,
                "personality": personality,
                "abilities": abilities,
                "history": history
            }

            st.session_state.characters.append(character)
            memory["characters"] = st.session_state.characters
            save_memory(memory)

            st.success(f"{name} has been saved!")
        else:
            st.warning("Please enter a character name.")

# Display saved characters
st.subheader("Saved Characters")

if st.session_state.characters:
    for character in st.session_state.characters:
        with st.expander(character["name"]):
            st.write("Age:", character["age"])
            st.write("Personality:", character["personality"])
            st.write("Abilities:", character["abilities"])
            st.write("History:", character["history"])
else:
    st.info("No characters saved yet.")

st.divider()

# World lore
st.header("2. World Lore Memory")

st.session_state.lore = st.text_area(
    "Enter important facts and rules about your fictional world",
    value=st.session_state.lore,
    height=150,
    placeholder="Example: Magic can only be used by people born with special abilities."
)
memory["lore"] = st.session_state.lore
save_memory(memory)

st.divider()


# ==========================================
# 3. AI CONTINUITY CHECKER
# ==========================================

st.header("3. AI Continuity Checker")

chapter_title = st.text_input(
    "Chapter title",
    placeholder="Example: The Burning Forest"
)

chapter = st.text_area(
    "Paste your new chapter here",
    height=250,
    placeholder="Paste your story chapter..."
)

if st.button("Analyze Story", type="primary", use_container_width=True):

    if not client:
        st.error("API key missing. Check your .env file.")

    elif not chapter.strip():
        st.warning("Please enter a story chapter.")

    elif not st.session_state.characters and not st.session_state.lore.strip():
        st.warning("Please add character information or world lore first.")

    else:

        character_memory = json.dumps(
            st.session_state.characters,
            ensure_ascii=False,
            indent=2
        )

        prompt = f"""
You are LoreGuard AI, an expert narrative consistency analyst.

Analyze the new chapter against the established fictional universe.

ESTABLISHED CHARACTERS:
{character_memory}

ESTABLISHED WORLD LORE:
{st.session_state.lore}

NEW CHAPTER:
{chapter}

Return ONLY valid JSON using exactly this structure:

{{
  "overall_result": "Consistent or Inconsistent",
  "summary": "Brief explanation of the analysis",
  "issues": [
    {{
      "type": "Physical, Personality, Historical, World Rule, or Other",
      "severity": "High, Medium, or Low",
      "certainty": "Definite or Possible",
      "title": "Short issue title",
      "description": "What happened in the new chapter",
      "evidence": "The established fact that conflicts with it",
      "explanation": "Why this may be inconsistent",
      "suggestion": "How the writer could improve it"
    }}
  ],
  "final_verdict": "Your final assessment"
}}

IMPORTANT RULES:

1. Only identify contradictions supported by established information.
2. Do not invent character history or world rules.
3. A missing piece of information is not automatically a contradiction.
4. Use Possible when more information is needed.
5. Use Definite only when the established facts clearly conflict.
6. Do not treat intentional character development as an error without evidence.

7. If there are no contradictions, return an empty issues array.

8. IMPORTANT: Check for missing character qualifications.

If a character performs an ability that has not
been established in their profile, compare it
against the world's rules.

For example:
- A character uses magic.
- World lore says only people born with
  magical abilities can use magic.
- The character's magical eligibility is unknown.

You MUST report this as a POSSIBLE inconsistency.

Do not classify missing information as a
definite contradiction.

9. Do not silently ignore potentially important
continuity concerns just because information is missing.

10. Return valid JSON without Markdown code fences.

11. STRICT EVIDENCE REQUIREMENT:

Never report an event that does not actually occur
in the new chapter.

Before reporting an issue, identify the exact action
performed by the character in the chapter.

Do not assume that a character used an ability
unless the chapter explicitly describes that ability.

12. NO INVENTED CONTRADICTIONS:

If Arin uses fire magic, never report that Arin
used water magic.

If a character's action is consistent with their
established abilities, do not report an issue.

13. DISTINGUISH EXHAUSTION FROM INCAPACITY:

If a character becomes exhausted after using magic,
this does not automatically mean they cannot
continue fighting.

Only report a contradiction if established world
rules explicitly prohibit the action.


14. CERTAINTY CLASSIFICATION — STRICT RULES

DEFINITE:
Use DEFINITE when BOTH conditions are true:
- The established character profile or world lore
  explicitly prohibits something.
- The submitted chapter explicitly shows that
  prohibited action happening.

Examples:
- Kael has no magic, but explicitly uses water magic.
  => DEFINITE.
- Healing cannot resurrect the dead, but Lyra
  explicitly brings a dead person back to life.
  => DEFINITE.

POSSIBLE:
Use POSSIBLE only when:
- The chapter evidence is ambiguous.
- The established lore is incomplete.
- The action might violate a rule, but the violation
  cannot be confirmed.

IMPORTANT:
Do not downgrade an explicitly proven contradiction
to POSSIBLE because of uncertainty about the
character's motives or the explanation behind it.

Before assigning certainty, compare the exact
chapter event with the exact established rule.

15. EVIDENCE VERIFICATION:

Every issue must contain:
- The exact event from the new chapter.
- The established character or world fact.
- A clear explanation of the conflict.

If the event cannot be supported by the chapter,
discard the issue.

16. FALSE POSITIVE PREVENTION:

Do not report:
- Events that never happened.
- Abilities a character never used.
- Normal character development.
- Actions that are unusual but not forbidden.
- Assumptions unsupported by established lore.

"""

        with st.spinner("LoreGuard is examining your story..."):

            try:
                response = client.models.generate_content(
                    model="gemini-3.5-flash-lite",
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json"
                    }
                )

                # Convert AI response into Python data
                report = json.loads(response.text)
                # Save the analyzed chapter permanently
                chapter_data = {
                    "title": chapter_title if chapter_title else "Untitled Chapter",
                    "content": chapter,
                    "report": report
                }

                save_chapter(chapter_data)

                st.success("Chapter and analysis saved permanently!")

                issues = report.get("issues", [])

                definite_count = sum(
                    1 for issue in issues
                    if issue.get("certainty", "").lower() == "definite"
                )

                possible_count = len(issues) - definite_count

                # ==================================
                # ANALYSIS DASHBOARD
                # ==================================

                st.divider()

                st.subheader("📊 Story Analysis Dashboard")

                st.write(
                    f"Analysis for: **{chapter_title or 'Untitled Chapter'}**"
                )

                result = report.get(
                    "overall_result", "Analysis completed"
                )

                if result.lower() == "consistent":
                    st.success("Your chapter appears consistent!")
                else:
                    st.warning("Potential continuity problems detected.")

                # Summary
                st.info(report.get("summary", "Analysis completed."))

                # Metrics
                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "Total Issues",
                    len(issues)
                )

                col2.metric(
                    "Definite Issues",
                    definite_count
                )

                col3.metric(
                    "Possible Issues",
                    possible_count
                )

                st.divider()

                st.subheader("🔎 Detected Inconsistencies")

                if not issues:
                    st.success(
                        "No contradictions were identified "
                        "against the supplied story memory."
                    )

                # Display individual issue cards
                for index, issue in enumerate(issues, start=1):

                    severity = issue.get(
                        "severity", "Medium"
                    ).lower()

                    certainty = issue.get(
                        "certainty", "Possible"
                    )

                    if severity == "high":
                        badge = "🔴 HIGH"
                    elif severity == "medium":
                        badge = "🟠 MEDIUM"
                    else:
                        badge = "🟡 LOW"

                    with st.container(border=True):

                        st.markdown(
                            f"### {index}. {issue.get('title', 'Story issue')}"
                        )

                        st.caption(
                            f"{issue.get('type', 'Other')} | "
                            f"{badge} | "
                            f"{certainty} finding"
                        )

                        st.markdown("**What happened?**")
                        st.write(
                            issue.get("description", "Not provided.")
                        )

                        st.markdown("**Established evidence**")
                        st.write(
                            issue.get("evidence", "Not provided.")
                        )

                        st.markdown("**Why is this a problem?**")
                        st.write(
                            issue.get("explanation", "Not provided.")
                        )

                        st.markdown("**💡 Suggested correction**")
                        st.success(
                            issue.get("suggestion", "No suggestion provided.")
                        )

                st.divider()

                st.subheader("📝 Final Verdict")

                st.write(
                    report.get(
                        "final_verdict",
                        "Analysis completed."
                    )
                )

                # Allow users to download their report
                report_json = json.dumps(
                    report,
                    indent=4,
                    ensure_ascii=False
                )

                st.download_button(
                    label="Download Analysis Report",
                    data=report_json,
                    file_name="loreguard_analysis.json",
                    mime="application/json",
                    use_container_width=True
                )

            except json.JSONDecodeError:
                st.error(
                    "The AI returned an invalid JSON response. "
                    "Please try analyzing the chapter again."
                )

            except Exception as error:
                st.error(f"Analysis failed: {error}")

st.divider()

st.caption("LoreGuard AI | Your Story. Your Universe. Always Consistent.")


# ==========================================
# 4. CHAPTER LIBRARY
# ==========================================

st.header("📚 Chapter Library")

# Load permanently saved chapters
saved_memory = load_memory()
saved_chapters = saved_memory.get("chapters", [])

if not saved_chapters:
    st.info("No analyzed chapters saved yet.")

else:
    st.write(
        f"You have {len(saved_chapters)} saved chapters."
    )

    for index, saved in enumerate(saved_chapters):

        report = saved.get("report", {})

        with st.expander(
            f"📖 {saved.get('title', 'Untitled Chapter')}"
        ):

            issues = report.get("issues", [])

            st.write(
                f"Total detected issues: {len(issues)}"
            )

            st.markdown("### Analysis Summary")

            st.write(
                report.get("summary", "No summary available.")
            )

            st.markdown("### Detected Issues")

            if issues:
                for issue in issues:
                    st.markdown(
                        f"**{issue.get('title', 'Issue')}**"
                    )

                    st.write(
                        issue.get("explanation", "")
                    )
            else:
                st.success("No inconsistencies detected.")

            st.markdown("### Original Chapter")

            st.text(saved.get("content", ""))

st.divider()
st.caption("LoreGuard AI | Your Story. Your Universe.")
