from datetime import datetime
import os

from dotenv import load_dotenv
load_dotenv()  # Load .env file

import gifos
from zoneinfo import ZoneInfo

FONT_FILE_BITMAP = "./fonts/CascadiaCode.ttf"
FONT_FILE_MONA = "./fonts/Inversionz.otf"


def main():
    t = gifos.Terminal(1000, 650, 15, 15, FONT_FILE_BITMAP, 15)
    
    # Set custom prompt
    t.set_prompt("\x1b[0;91meiyuumiru\x1b[0m@\x1b[0;93mgifos ~> \x1b[0m")

    year_now = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%Y")
    time_now = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).strftime(
        "%a %b %d %I:%M:%S %p %Z %Y"
    )

    # Fetch GitHub stats
    ignore_repos = []  # Add repos to ignore if needed
    git_user_details = gifos.utils.fetch_github_stats("eiyuumiru", ignore_repos)
    user_age = gifos.utils.calc_age(28, 3, 2006)  # Birthday: 28/03/2006
    
    top_languages = [lang[0] for lang in git_user_details.languages_sorted]
    
    # Neofetch-style user details
    user_details_lines = f"""
    \\x1b[30;101meiyuumiru@GitHub\\x1b[0m
    ----------------
    \\x1b[96mOS:     \\x1b[93mWindows 11, Arch Linux, iOS 26\\x1b[0m
    \\x1b[96mHost:   \\x1b[93mUniversity of Information Technology (UIT)\\x1b[0m
    \\x1b[96mKernel: \\x1b[93mComputer Science\\x1b[0m
    \\x1b[96mUptime: \\x1b[93m{user_age.years} years, {user_age.months} months, {user_age.days} days\\x1b[0m
    \\x1b[96mIDE:    \\x1b[93mVSCode, Cursor\\x1b[0m
    
    \\x1b[30;101mContact:\\x1b[0m
    ----------------
    \\x1b[96mEmail:      \\x1b[93m24521352@gm.uit.edu.vn\\x1b[0m
    \\x1b[96mLinkedIn:   \\x1b[93meiyuumiru\\x1b[0m
    
    \\x1b[30;101mGitHub Stats:\\x1b[0m
    ----------------
    \\x1b[96mUser Rating: \\x1b[93m{git_user_details.user_rank.level}\\x1b[0m
    \\x1b[96mTotal Stars Earned: \\x1b[93m{git_user_details.total_stargazers}\\x1b[0m
    \\x1b[96mTotal Commits ({int(year_now) - 1}): \\x1b[93m{git_user_details.total_commits_last_year}\\x1b[0m
    \\x1b[96mTotal PRs: \\x1b[93m{git_user_details.total_pull_requests_made}\\x1b[0m
    \\x1b[96mMerged PR %: \\x1b[93m{git_user_details.pull_requests_merge_percentage}\\x1b[0m
    \\x1b[96mTotal Contributions: \\x1b[93m{git_user_details.total_repo_contributions}\\x1b[0m
    \\x1b[96mTop Languages: \\x1b[93m{', '.join(top_languages[:5])}\\x1b[0m
    """

    # Generate prompt and neofetch command
    t.toggle_show_cursor(False)
    t.gen_prompt(1)
    prompt_col = t.curr_col
    t.toggle_show_cursor(True)
    t.gen_typing_text("\\x1b[92mneofetch\\x1b[0m", 1, contin=True)
    t.gen_text("", 2, count=5)

    # Mona ASCII art (GitHub mascot)
    t.set_font(FONT_FILE_MONA, 16, 0)
    t.toggle_show_cursor(False)
    monaLines = r"""
    \x1b[49m     \x1b[90;100m}}\x1b[49m     \x1b[90;100m}}\x1b[0m
    \x1b[49m    \x1b[90;100m}}}}\x1b[49m   \x1b[90;100m}}}}\x1b[0m
    \x1b[49m    \x1b[90;100m}}}}}\x1b[49m \x1b[90;100m}}}}}\x1b[0m
    \x1b[49m   \x1b[90;100m}}}}}}}}}}}}}\x1b[0m
    \x1b[49m   \x1b[90;100m}}}}}}}}}}}}}}\x1b[0m
    \x1b[49m   \x1b[90;100m}}\x1b[37;47m}}}}}}}\x1b[90;100m}}}}}\x1b[0m
    \x1b[49m  \x1b[90;100m}}\x1b[37;47m}}}}}}}}}}\x1b[90;100m}}}\x1b[0m
    \x1b[49m  \x1b[90;100m}}\x1b[37;47m}\x1b[90;100m}\x1b[37;47m}}}}}\x1b[90;100m}\x1b[37;47m}}\x1b[90;100m}}}}\x1b[0m
    \x1b[49m  \x1b[90;100m}\x1b[37;47m}}\x1b[90;100m}\x1b[37;47m}}}}}\x1b[90;100m}\x1b[37;47m}}}\x1b[90;100m}}}\x1b[0m
    \x1b[90;100m}}}\x1b[37;47m}}}}\x1b[90;100m}}}\x1b[37;47m}}}}}\x1b[90;100m}}}}\x1b[0m
    \x1b[49m  \x1b[90;100m}\x1b[37;47m}}}}}\x1b[90;100m}}\x1b[37;47m}}}}}\x1b[90;100m}}}\x1b[0m
    \x1b[49m \x1b[90;100m}}\x1b[37;47m}}}}}}}}}}}}\x1b[90;100m}}}\x1b[0m
    \x1b[90;100m}\x1b[49m  \x1b[90;100m}}\x1b[37;47m}}}}}}}}\x1b[90;100m}}}\x1b[49m  \x1b[90;100m}\x1b[0m
    \x1b[49m        \x1b[90;100m}}}}}\x1b[0m
    \x1b[49m       \x1b[90;100m}}}}}}}\x1b[0m
    \x1b[49m       \x1b[90;100m}}}}}}}}\x1b[0m
    \x1b[49m      \x1b[90;100m}}}}}}}}}}\x1b[0m
    \x1b[49m     \x1b[90;100m}}}}}}}}}}}\x1b[0m
    \x1b[49m     \x1b[90;100m}}}}}}}}}}}}\x1b[0m
    \x1b[49m     \x1b[90;100m}}\x1b[49m \x1b[90;100m}}}}}}\x1b[49m \x1b[90;100m}}\x1b[0m
    \x1b[49m        \x1b[90;100m}}}}}}}\x1b[0m
    \x1b[49m         \x1b[90;100m}}}\x1b[49m \x1b[90;100m}}\x1b[0m
    """
    t.gen_text(monaLines, 3)

    # User details next to Mona
    t.set_font(FONT_FILE_BITMAP)
    t.toggle_show_cursor(True)
    t.gen_text(user_details_lines, 2, 35, count=5, contin=True)
    
    # Final prompt with message
    t.gen_prompt(t.curr_row)
    t.gen_typing_text(
        "\\x1b[92m# Have a nice day :D",
        t.curr_row,
        contin=True,
    )
    t.gen_text("", t.curr_row, count=120, contin=True)

    # Generate GIF
    t.gen_gif()
    
    # Generate README.md
    readme_file_content = rf"""<div align="justify">
<picture>
    <source media="(prefers-color-scheme: dark)" srcset="./output.gif">
    <source media="(prefers-color-scheme: light)" srcset="./output.gif">
    <img alt="GIFOS" src="output.gif">
</picture>
</div>"""
    
    with open("README.md", "w") as f:
        f.write(readme_file_content)
        print("INFO: README.md file generated")


if __name__ == "__main__":
    main()
