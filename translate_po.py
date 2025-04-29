import polib
from googletrans import Translator
import sys
import time
import argparse

def translate_po_file(filepath):
    """
    Translates empty msgstr entries in a .po file to Arabic using googletrans,
    skipping entries where associated occurrences (#: comments) contain 'report'
    or entries that are marked as fuzzy or already translated.

    Args:
        filepath (str): The path to the .po file.
    """
    try:
        po = polib.pofile(filepath)
        translator = Translator()
        target_language = 'ar' # Arabic

        print(f"Processing file: {filepath}")
        print(f"Found {len(po)} entries.")

        translated_count = 0
        skipped_count = 0
        entries_to_translate = []

        # Pre-filter entries to potentially translate
        potentially_translatable = [entry for entry in po if not entry.msgstr and entry.msgid]
        print(f"Found {len(potentially_translatable)} entries with empty msgstr.")

        for entry in potentially_translatable:
            skip_entry = False

            # 1. Skip if 'report' is in occurrences (#: comments)
            if hasattr(entry, 'occurrences') and entry.occurrences:
                for filename, line_num_str in entry.occurrences:
                    if 'report' in filename.lower():
                        print(f"Skipping entry (line {entry.linenum}) due to 'report' in occurrences: {filename}")
                        skip_entry = True
                        break # Found report, no need to check other occurrences

            if skip_entry:
                skipped_count += 1
                continue

            # 2. Skip fuzzy entries (already handled by initial check, but good to keep explicit)
            if 'fuzzy' in entry.flags:
                print(f"Skipping fuzzy entry (line {entry.linenum}): {entry.msgid[:50]}...")
                skipped_count += 1
                continue

            # If not skipped for any reason, add to the list for translation
            entries_to_translate.append(entry)

        print(f"Attempting to translate {len(entries_to_translate)} entries.")

        for i, entry in enumerate(entries_to_translate):
            original_text = entry.msgid
            print(f"Translating ({i+1}/{len(entries_to_translate)}): {original_text[:50]}...")
            try:
                # Add a small delay to avoid hitting rate limits
                time.sleep(0.5) # Adjust delay as needed
                translation = translator.translate(original_text, dest=target_language)
                if translation and translation.text:
                    entry.msgstr = translation.text
                    # Remove fuzzy flag if we successfully translated it
                    if 'fuzzy' in entry.flags:
                        entry.flags.remove('fuzzy')
                    translated_count += 1
                    print(f"  -> Translated to: {entry.msgstr[:50]}...")
                else:
                    print(f"  -> Translation failed or returned empty for: {original_text[:50]}...")
            except Exception as e:
                print(f"  -> Error translating '{original_text[:50]}...': {e}")
                # Optional: break or continue on error
                continue # Continue with the next entry

        if translated_count > 0:
            print(f"Saving translated file: {filepath}")
            po.save()
            # Optional: Compile .po to .mo if needed
            # po.save_as_mofile(filepath.replace('.po', '.mo'))
            print(f"Successfully translated {translated_count} new entries.")
        else:
            print("No new entries were translated in this run.")

        if skipped_count > 0:
            print(f"Skipped a total of {skipped_count} entries (already translated, fuzzy, or report-related)." + 
                  f" Note: The count includes entries skipped in the initial filter.")

    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Translate .po file entries to Arabic, skipping report-related, fuzzy, or already translated entries.')
    parser.add_argument('filepath', type=str, nargs='?', default=None, help='Path to the .po file to translate (optional).')

    args = parser.parse_args()
    filepath = args.filepath

    if filepath is None:
        # Default path if no argument is provided - adjust if necessary
        filepath = '/opt/odoo18/projects/bb/bbb/i18n/ar_001.po'
        print(f"No filepath provided via command line. Using default: {filepath}")

    translate_po_file(filepath)
