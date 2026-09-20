# Workflow reference

Run project-setup with no arguments for the step-by-step guide.
Create with --project NAME --proj-dir PARENT --objective "Scientific task".
Git is initialized first; the initial scaffold is committed when identity exists.
Follow the generated startup-prompt.txt with your coding agent.
Read README.md or docs/index.html for the complete 1.0.0 reference.

Each new project includes script/project-update. It uses version/VERSION and
version/dist; legacy projects with root VERSION continue using versions/.
Keep the project lock while an agent works; supply --session to its updater.
Full HTML/TXT user manuals are generated only when requested through an external
project-document installation. No documentation tool is bundled.
