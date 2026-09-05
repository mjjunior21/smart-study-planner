"""
Smart Study Planner
-------------------
A console based study session tracker.

The programme lets a student log study sessions, view them in a table,
search them by subject, analyse study statistics, and it stores everything
in a plain text file (study_log.txt) so that data survives between runs.

Each session is held in memory as a dictionary:
    {"subject": str, "topic": str, "date": str, "duration": float}
and all sessions are held in a single list.
"""

DATA_FILE = "study_log.txt"
FIELD_SEP = "|"          # separator used inside the text file
SHORT_LIMIT = 30         # minutes: below this a session is "Short"
LONG_LIMIT = 90          # minutes: above this a session is "Long"


# ----------------------------------------------------------------------
# Small helper utilities
# ----------------------------------------------------------------------

def clean_text(text, fallback="Unknown"):
    """
    Tidy up free text typed by the user.

    The pipe character is removed because it is used as the field separator
    in study_log.txt; leaving it in would corrupt the saved records.
    """
    text = text.replace(FIELD_SEP, "/").strip()
    return text if text else fallback


def fit(text, width):
    """Trim text so that it fits a fixed width table column."""
    text = str(text)
    if len(text) <= width:
        return text
    return text[:width - 3] + "..."


def format_duration(minutes):
    """Show 45 instead of 45.0, but keep 45.5 as 45.5."""
    if float(minutes).is_integer():
        return str(int(minutes))
    return str(round(float(minutes), 1))


def prompt_positive_number(message):
    """
    Keep asking until the user supplies a number greater than zero.

    Anything that cannot be converted to a float (letters, blanks, symbols)
    is rejected with a message instead of crashing the programme.
    """
    while True:
        raw = input(message).strip()
        try:
            value = float(raw)
        except ValueError:
            print("  Invalid input. Please enter a number, for example 45.")
            continue
        if value <= 0:
            print("  Duration must be greater than zero. Please try again.")
            continue
        return value


# ----------------------------------------------------------------------
# (g) File handling: load and save
# ----------------------------------------------------------------------

def load_sessions(filename=DATA_FILE):
    """
    Read saved sessions from the data file and return them as a list.

    If the file does not exist yet (the very first run) an empty list is
    returned instead of raising an error. Records that are damaged or
    incomplete are skipped so that one bad line cannot stop the programme.
    """
    sessions = []
    try:
        with open(filename, "r", encoding="utf-8") as file_handle:
            for line_number, line in enumerate(file_handle, start=1):
                line = line.strip()
                if not line:
                    continue
                parts = line.split(FIELD_SEP)
                if len(parts) != 4:
                    print("Warning: skipping damaged record on line "
                          + str(line_number) + ".")
                    continue
                subject, topic, date, duration_text = parts
                try:
                    duration = float(duration_text)
                except ValueError:
                    print("Warning: skipping record with a bad duration on "
                          "line " + str(line_number) + ".")
                    continue
                if duration <= 0:
                    print("Warning: skipping record with a non-positive "
                          "duration on line " + str(line_number) + ".")
                    continue
                sessions.append({
                    "subject": subject,
                    "topic": topic,
                    "date": date,
                    "duration": duration
                })
    except FileNotFoundError:
        # Normal on the first run. Start with an empty planner.
        return []
    except OSError as error:
        print("Could not read " + filename + ": " + str(error))
        return []
    return sessions


def save_sessions(sessions, filename=DATA_FILE):
    """Write every session to the data file, one record per line."""
    try:
        with open(filename, "w", encoding="utf-8") as file_handle:
            for session in sessions:
                record = FIELD_SEP.join([
                    session["subject"],
                    session["topic"],
                    session["date"],
                    format_duration(session["duration"])
                ])
                file_handle.write(record + "\n")
    except OSError as error:
        print("Could not save to " + filename + ": " + str(error))
        return False
    return True


# ----------------------------------------------------------------------
# (c) Classification
# ----------------------------------------------------------------------

def classify_session(duration):
    """
    Return "Short", "Medium" or "Long" for a session length in minutes.

    Short  : under 30 minutes
    Medium : 30 to 90 minutes inclusive
    Long   : over 90 minutes
    """
    if duration < SHORT_LIMIT:
        return "Short"
    elif duration <= LONG_LIMIT:
        return "Medium"
    else:
        return "Long"


# ----------------------------------------------------------------------
# (b) Adding a session
# ----------------------------------------------------------------------

def add_session(sessions):
    """Collect one study session from the user and append it to the list."""
    print("\n--- Add a study session ---")
    subject = clean_text(input("Subject               : "), "Unspecified")
    topic = clean_text(input("Topic covered         : "), "General revision")
    date = clean_text(input("Date or day label     : "), "Not dated")
    duration = prompt_positive_number("Duration in minutes   : ")

    session = {
        "subject": subject,
        "topic": topic,
        "date": date,
        "duration": duration
    }
    sessions.append(session)
    save_sessions(sessions)

    print("\nSession saved: " + subject + " for "
          + format_duration(duration) + " minutes ("
          + classify_session(duration) + ").")


# ----------------------------------------------------------------------
# (d) Viewing sessions
# ----------------------------------------------------------------------

def print_table_header():
    """Print the shared header used by the view and search tables."""
    print("{:<3} {:<16} {:<26} {:<12} {:>10} {:<8}".format(
        "No", "Subject", "Topic", "Date", "Minutes", "Type"))
    print("-" * 80)


def print_session_row(index, session):
    """Print one session as a single formatted table row."""
    print("{:<3} {:<16} {:<26} {:<12} {:>10} {:<8}".format(
        index,
        fit(session["subject"], 16),
        fit(session["topic"], 26),
        fit(session["date"], 12),
        format_duration(session["duration"]),
        classify_session(session["duration"])))


def view_sessions(sessions):
    """Display every logged session in a formatted table."""
    print("\n--- All study sessions ---")
    if not sessions:
        print("No sessions have been logged yet. Use option 1 to add one.")
        return

    print_table_header()
    total = 0.0
    for position, session in enumerate(sessions, start=1):
        print_session_row(position, session)
        total += session["duration"]
    print("-" * 80)
    print("Total sessions: " + str(len(sessions))
          + "    Total time: " + format_duration(total)
          + " minutes (" + str(round(total / 60, 2)) + " hours)")


# ----------------------------------------------------------------------
# (e) Searching by subject
# ----------------------------------------------------------------------

def search_by_subject(sessions, subject):
    """
    Display only the sessions belonging to one subject.

    Matching ignores capitalisation and surrounding spaces, so "MATHS",
    "maths" and " Maths " all find the same records.
    """
    target = subject.strip().lower()
    matches = [s for s in sessions if s["subject"].strip().lower() == target]

    print("\n--- Sessions for '" + subject.strip() + "' ---")
    if not matches:
        print("No study sessions have been recorded for that subject.")
        return matches

    print_table_header()
    total = 0.0
    for position, session in enumerate(matches, start=1):
        print_session_row(position, session)
        total += session["duration"]
    print("-" * 80)
    print("Sessions found: " + str(len(matches))
          + "    Total time on this subject: " + format_duration(total)
          + " minutes (" + str(round(total / 60, 2)) + " hours)")
    return matches


# ----------------------------------------------------------------------
# (f) Statistics
# ----------------------------------------------------------------------

def totals_per_subject(sessions):
    """
    Build a dictionary of {subject: total minutes}.

    Subjects are grouped case insensitively, but the first spelling the
    student used is kept for display purposes.
    """
    totals = {}
    labels = {}
    for session in sessions:
        key = session["subject"].strip().lower()
        totals[key] = totals.get(key, 0.0) + session["duration"]
        if key not in labels:
            labels[key] = session["subject"].strip()
    return {labels[key]: minutes for key, minutes in totals.items()}


def study_statistics(sessions):
    """Display overall totals, per subject totals, weakest area and longest session."""
    print("\n--- Study statistics ---")
    if not sessions:
        print("No sessions have been logged yet, so there is nothing to analyse.")
        return

    overall_minutes = sum(s["duration"] for s in sessions)
    print("Total sessions logged : " + str(len(sessions)))
    print("Total time studied    : " + format_duration(overall_minutes)
          + " minutes (" + str(round(overall_minutes / 60, 2)) + " hours)")
    print("Average session length: "
          + str(round(overall_minutes / len(sessions), 1)) + " minutes")

    totals = totals_per_subject(sessions)

    print("\nHours studied per subject:")
    print("{:<20} {:>12} {:>10}".format("Subject", "Minutes", "Hours"))
    print("-" * 44)
    # Sort from most studied to least so the weakest area sits at the bottom
    for subject, minutes in sorted(totals.items(), key=lambda item: item[1],
                                   reverse=True):
        print("{:<20} {:>12} {:>10}".format(
            fit(subject, 20), format_duration(minutes), round(minutes / 60, 2)))

    # Weakest area: the subject with the smallest total study time
    weakest = min(totals.items(), key=lambda item: item[1])
    print("\nWeakest area (least total study time): " + weakest[0]
          + " with only " + format_duration(weakest[1]) + " minutes ("
          + str(round(weakest[1] / 60, 2)) + " hours)")

    # Longest single session recorded
    longest = max(sessions, key=lambda s: s["duration"])
    print("Longest single session: " + format_duration(longest["duration"])
          + " minutes on " + longest["subject"] + " ("
          + longest["topic"] + ", " + longest["date"] + ") classified as "
          + classify_session(longest["duration"]) + ".")


# ----------------------------------------------------------------------
# (a) Menu driven interface
# ----------------------------------------------------------------------

def display_menu():
    """Print the main menu options."""
    print("\n" + "=" * 44)
    print("        SMART STUDY PLANNER")
    print("=" * 44)
    print("1. Add a study session")
    print("2. View all sessions")
    print("3. Search sessions by subject")
    print("4. View statistics")
    print("5. Save and exit")
    print("=" * 44)


def main():
    """Run the planner until the user chooses to save and exit."""
    sessions = load_sessions()
    if sessions:
        print("Loaded " + str(len(sessions)) + " saved session(s) from "
              + DATA_FILE + ".")
    else:
        print("No previous data found. Starting a fresh study log.")

    try:
        while True:
            display_menu()
            choice = input("Choose an option (1-5): ").strip()

            if choice == "1":
                add_session(sessions)
            elif choice == "2":
                view_sessions(sessions)
            elif choice == "3":
                subject = input("\nEnter the subject to search for: ")
                if subject.strip():
                    search_by_subject(sessions, subject)
                else:
                    print("No subject entered. Returning to the menu.")
            elif choice == "4":
                study_statistics(sessions)
            elif choice == "5":
                if save_sessions(sessions):
                    print("\n" + str(len(sessions)) + " session(s) saved to "
                          + DATA_FILE + ". Goodbye.")
                break
            else:
                # Invalid choices are reported and the menu simply reappears
                print("Invalid choice. Please enter a number between 1 and 5.")
    except (KeyboardInterrupt, EOFError):
        print("\n\nInterrupted. Saving your data before exiting...")
        if save_sessions(sessions):
            print(str(len(sessions)) + " session(s) saved to "
                  + DATA_FILE + ". Goodbye.")


if __name__ == "__main__":
    main()
