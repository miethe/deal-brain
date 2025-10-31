#!/usr/bin/env python3
"""
Interactive Symbols Configuration Wizard

Creates a customized symbols.config.json for your project with an interactive CLI.
Supports multiple project templates and allows customization of all settings.

Usage:
    # Interactive mode (recommended)
    python .claude/skills/symbols/scripts/init_symbols.py

    # Quick setup with template
    python .claude/skills/symbols/scripts/init_symbols.py --template=react-typescript-fullstack

    # Non-interactive with all options
    python .claude/skills/symbols/scripts/init_symbols.py \\
      --template=python-fastapi \\
      --name="MyProject" \\
      --symbols-dir="ai" \\
      --force

    # List available templates
    python .claude/skills/symbols/scripts/init_symbols.py --list

    # Dry run (preview without writing)
    python .claude/skills/symbols/scripts/init_symbols.py --dry-run

Features:
    - Interactive CLI with input validation
    - 5 project templates (React, FastAPI, Next.js, Vue, Django)
    - Customizable domains, layers, and extraction paths
    - Schema validation before writing
    - Color output for better UX (when colorama available)
    - Non-interactive mode for automation
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

# Try to import colorama for colored output
try:
    from colorama import init as colorama_init, Fore, Style

    colorama_init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    # Fallback to no color
    class Fore:
        GREEN = RED = YELLOW = BLUE = CYAN = MAGENTA = WHITE = ""

    class Style:
        BRIGHT = RESET_ALL = ""

    HAS_COLOR = False


# Template metadata
TEMPLATES = {
    "react-typescript-fullstack": {
        "name": "React + TypeScript Fullstack",
        "description": "React + TypeScript monorepo with FastAPI backend",
        "file": "react-typescript-fullstack.json",
        "frameworks": "React, Next.js, FastAPI, SQLAlchemy",
        "best_for": "Full-stack monorepos with React frontend and Python backend",
    },
    "nextjs-monorepo": {
        "name": "Next.js Monorepo",
        "description": "Next.js monorepo with App Router",
        "file": "nextjs-monorepo.json",
        "frameworks": "Next.js 14+, React, Tailwind, Turborepo",
        "best_for": "Next.js applications with multiple apps and shared packages",
    },
    "python-fastapi": {
        "name": "Python FastAPI",
        "description": "FastAPI backend with SQLAlchemy",
        "file": "python-fastapi.json",
        "frameworks": "FastAPI, SQLAlchemy, Pydantic, Alembic",
        "best_for": "Python API services with layered architecture",
    },
    "python-django": {
        "name": "Python Django",
        "description": "Django web framework",
        "file": "python-django.json",
        "frameworks": "Django, Django REST Framework",
        "best_for": "Django applications with MVT architecture",
    },
    "vue-typescript": {
        "name": "Vue + TypeScript",
        "description": "Vue 3 application with TypeScript",
        "file": "vue-typescript.json",
        "frameworks": "Vue 3, Composition API, Pinia, Vite",
        "best_for": "Vue applications with TypeScript and modern tooling",
    },
}


def print_header(text: str, char: str = "=") -> None:
    """Print a formatted header."""
    width = 80
    print()
    print(f"{Fore.CYAN}{Style.BRIGHT}{char * width}")
    print(f"{text:^{width}}")
    print(f"{char * width}{Style.RESET_ALL}")
    print()


def print_success(text: str) -> None:
    """Print success message."""
    print(f"{Fore.GREEN}✓ {text}{Style.RESET_ALL}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"{Fore.RED}✗ {text}{Style.RESET_ALL}", file=sys.stderr)


def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"{Fore.YELLOW}⚠ {text}{Style.RESET_ALL}")


def print_info(text: str) -> None:
    """Print info message."""
    print(f"{Fore.BLUE}ℹ {text}{Style.RESET_ALL}")


def print_step(number: int, text: str) -> None:
    """Print step number and description."""
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}Step {number}: {text}{Style.RESET_ALL}")


def get_templates_dir() -> Path:
    """Get the templates directory path."""
    script_dir = Path(__file__).parent
    return script_dir.parent / "templates"


def get_schema_path() -> Path:
    """Get the schema file path."""
    script_dir = Path(__file__).parent
    return script_dir.parent / "symbols-config-schema.json"


def find_project_root() -> Path:
    """
    Find the project root directory.

    Looks for common markers like .git, package.json, pyproject.toml.
    """
    search_path = Path.cwd()
    for _ in range(10):  # Limit search depth
        # Check for common project root markers
        if any(
            (search_path / marker).exists()
            for marker in [".git", "package.json", "pyproject.toml", "setup.py"]
        ):
            return search_path

        if search_path == search_path.parent:
            break

        search_path = search_path.parent

    # Fallback to current directory
    return Path.cwd()


def detect_project_name() -> str:
    """Detect project name from git or directory name."""
    project_root = find_project_root()

    # Try to get from git config
    git_config = project_root / ".git" / "config"
    if git_config.exists():
        try:
            with open(git_config) as f:
                for line in f:
                    if "url = " in line:
                        # Extract repo name from URL
                        url = line.split("url = ")[1].strip()
                        # Handle both HTTPS and SSH URLs
                        if "/" in url:
                            name = url.split("/")[-1]
                            # Remove .git suffix
                            name = name.replace(".git", "")
                            if name:
                                return name
        except Exception:
            pass

    # Fallback to directory name
    return project_root.name


def validate_project_name(name: str) -> bool:
    """Validate project name (alphanumeric, hyphens, underscores)."""
    return bool(re.match(r"^[a-zA-Z0-9_-]+$", name))


def validate_directory(directory: str) -> bool:
    """Validate directory name (no leading/trailing slashes)."""
    return bool(re.match(r"^[^/].*[^/]$", directory)) or directory in [".", ""]


def list_templates() -> None:
    """List all available templates with details."""
    print_header("Available Templates")

    for template_id, meta in TEMPLATES.items():
        print(f"{Fore.CYAN}{Style.BRIGHT}{template_id}{Style.RESET_ALL}")
        print(f"  Name: {meta['name']}")
        print(f"  Description: {meta['description']}")
        print(f"  Frameworks: {meta['frameworks']}")
        print(f"  Best for: {meta['best_for']}")
        print()


def load_template(template_id: str) -> Dict[str, Any]:
    """Load a template configuration."""
    templates_dir = get_templates_dir()
    template_file = templates_dir / TEMPLATES[template_id]["file"]

    if not template_file.exists():
        raise FileNotFoundError(f"Template file not found: {template_file}")

    with open(template_file) as f:
        return json.load(f)


def replace_placeholders(config: Dict[str, Any], project_name: str, symbols_dir: str) -> Dict[str, Any]:
    """Replace placeholders in template configuration."""
    config_str = json.dumps(config)
    config_str = config_str.replace("{{PROJECT_NAME}}", project_name)
    config_str = config_str.replace("{{SYMBOLS_DIR}}", symbols_dir)
    return json.loads(config_str)


def validate_against_schema(config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate configuration against JSON schema.

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Try to import jsonschema
        import jsonschema
    except ImportError:
        print_warning("jsonschema not installed - skipping schema validation")
        print_info("Install with: pip install jsonschema")
        return True, None

    schema_path = get_schema_path()
    if not schema_path.exists():
        return True, "Schema file not found - skipping validation"

    try:
        with open(schema_path) as f:
            schema = json.load(f)

        jsonschema.validate(config, schema)
        return True, None
    except jsonschema.ValidationError as e:
        return False, f"Schema validation failed: {e.message}"
    except Exception as e:
        return False, f"Validation error: {e}"


def prompt_input(prompt: str, default: Optional[str] = None) -> str:
    """Prompt user for input with optional default."""
    if default:
        prompt_text = f"{prompt} [{Fore.GREEN}{default}{Style.RESET_ALL}]: "
    else:
        prompt_text = f"{prompt}: "

    response = input(prompt_text).strip()
    return response if response else (default or "")


def prompt_yes_no(prompt: str, default: bool = True) -> bool:
    """Prompt user for yes/no input."""
    default_str = "Y/n" if default else "y/N"
    response = input(f"{prompt} [{default_str}]: ").strip().lower()

    if not response:
        return default

    return response in ["y", "yes"]


def show_welcome() -> bool:
    """Show welcome screen and confirm user wants to proceed."""
    print_header("Symbols Skill Configuration Wizard")

    print(f"{Fore.CYAN}Welcome to the Symbols Configuration Wizard!{Style.RESET_ALL}")
    print()
    print("This wizard will help you set up symbol extraction for your project.")
    print()
    print(f"{Style.BRIGHT}What are symbols?{Style.RESET_ALL}")
    print("  • Pre-generated metadata about your codebase (functions, classes, types)")
    print("  • Enable token-efficient code navigation and analysis")
    print("  • 95-99% token reduction compared to reading full files")
    print()
    print(f"{Style.BRIGHT}Benefits:{Style.RESET_ALL}")
    print("  • Fast codebase exploration (0.1s vs 2-3 min)")
    print("  • Precise file:line references for navigation")
    print("  • Domain-chunked for targeted queries")
    print("  • Architectural awareness (layers, components, tests)")
    print()

    return prompt_yes_no("Would you like to continue?", default=True)


def select_template(non_interactive: bool = False, template_arg: Optional[str] = None) -> str:
    """Select a project template."""
    print_step(1, "Template Selection")

    if non_interactive and template_arg:
        if template_arg not in TEMPLATES:
            print_error(f"Invalid template: {template_arg}")
            print_info("Use --list to see available templates")
            sys.exit(1)
        print_success(f"Using template: {TEMPLATES[template_arg]['name']}")
        return template_arg

    print("Available templates:")
    print()

    template_list = list(TEMPLATES.keys())
    for i, template_id in enumerate(template_list, 1):
        meta = TEMPLATES[template_id]
        print(f"{Fore.CYAN}{i}.{Style.RESET_ALL} {Style.BRIGHT}{meta['name']}{Style.RESET_ALL}")
        print(f"   {meta['description']}")
        print(f"   Frameworks: {meta['frameworks']}")
        print()

    while True:
        choice = prompt_input(
            f"Select a template (1-{len(template_list)})",
            default="1"
        )

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(template_list):
                selected = template_list[idx]
                print_success(f"Selected: {TEMPLATES[selected]['name']}")
                return selected
        except ValueError:
            pass

        print_error("Invalid choice. Please enter a number between 1 and 5.")


def customize_project(
    template_id: str,
    non_interactive: bool = False,
    project_name_arg: Optional[str] = None,
    symbols_dir_arg: Optional[str] = None,
) -> tuple[str, str]:
    """Customize project name and symbols directory."""
    print_step(2, "Project Customization")

    # Project name
    default_name = detect_project_name()
    if non_interactive and project_name_arg:
        project_name = project_name_arg
    else:
        print()
        print_info(f"Detected project name from git/directory: {default_name}")
        project_name = prompt_input("Project name", default=default_name)

    while not validate_project_name(project_name):
        print_error("Invalid project name. Use only letters, numbers, hyphens, and underscores.")
        project_name = prompt_input("Project name", default=default_name)

    # Symbols directory
    default_symbols_dir = "ai"
    if non_interactive and symbols_dir_arg:
        symbols_dir = symbols_dir_arg
    else:
        print()
        print_info("The symbols directory will store all symbol files")
        symbols_dir = prompt_input("Symbols directory", default=default_symbols_dir)

    while not validate_directory(symbols_dir):
        print_error("Invalid directory. No leading or trailing slashes.")
        symbols_dir = prompt_input("Symbols directory", default=default_symbols_dir)

    print()
    print_success(f"Project: {project_name}")
    print_success(f"Symbols directory: {symbols_dir}")

    return project_name, symbols_dir


def preview_configuration(config: Dict[str, Any]) -> None:
    """Preview the configuration before writing."""
    print_step(3, "Configuration Preview")

    print()
    print(f"{Style.BRIGHT}Project Configuration:{Style.RESET_ALL}")
    print(f"  Project Name: {config['projectName']}")
    print(f"  Symbols Directory: {config['symbolsDir']}")
    print()

    print(f"{Style.BRIGHT}Domains:{Style.RESET_ALL}")
    for domain, domain_config in config["domains"].items():
        enabled = "✓" if domain_config.get("enabled", True) else "✗"
        print(f"  {enabled} {domain}: {domain_config['file']}")
        print(f"     {domain_config['description']}")

    if "apiLayers" in config and config["apiLayers"]:
        print()
        print(f"{Style.BRIGHT}API Layers:{Style.RESET_ALL}")
        for layer, layer_config in config["apiLayers"].items():
            enabled = "✓" if layer_config.get("enabled", True) else "✗"
            print(f"  {enabled} {layer}: {layer_config['file']}")
            print(f"     {layer_config['description']}")

    print()
    print(f"{Style.BRIGHT}Extraction Directories:{Style.RESET_ALL}")
    for lang, extraction in config["extraction"].items():
        print(f"  {lang.capitalize()}:")
        for directory in extraction["directories"]:
            print(f"    • {directory}")

    print()


def write_configuration(
    config: Dict[str, Any],
    output_path: Path,
    dry_run: bool = False,
    force: bool = False,
) -> bool:
    """
    Write configuration to file.

    Returns:
        True if written successfully, False otherwise
    """
    print_step(4, "Writing Configuration" if not dry_run else "Dry Run")

    # Update metadata
    if "metadata" not in config:
        config["metadata"] = {}

    config["metadata"]["lastUpdated"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if "version" not in config["metadata"]:
        config["metadata"]["version"] = "1.0"

    # Validate against schema
    is_valid, error = validate_against_schema(config)
    if not is_valid:
        print_error(f"Configuration validation failed: {error}")
        return False

    print_success("Configuration validated against schema")

    # Check if file exists
    if output_path.exists() and not force and not dry_run:
        print_warning(f"Configuration file already exists: {output_path}")
        if not prompt_yes_no("Overwrite existing configuration?", default=False):
            print_info("Aborted. Use --force to overwrite without prompting.")
            return False

    if dry_run:
        print()
        print_info("Dry run mode - configuration not written")
        print()
        print(f"{Style.BRIGHT}Configuration preview:{Style.RESET_ALL}")
        print(json.dumps(config, indent=2))
        return True

    # Create directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write configuration
    try:
        with open(output_path, "w") as f:
            json.dump(config, f, indent=2)
            f.write("\n")  # Add trailing newline

        print()
        print_success(f"Configuration written to: {output_path}")
        return True
    except Exception as e:
        print_error(f"Failed to write configuration: {e}")
        return False


def show_next_steps(config: Dict[str, Any], output_path: Path) -> None:
    """Show next steps after configuration is created."""
    print()
    print_header("Next Steps", char="-")

    symbols_dir = config["symbolsDir"]
    has_python = "python" in config["extraction"]
    has_typescript = "typescript" in config["extraction"]

    print(f"{Style.BRIGHT}1. Generate Symbols:{Style.RESET_ALL}")
    if has_typescript:
        print(f"   {Fore.CYAN}python .claude/skills/symbols/scripts/extract_symbols_typescript.py{Style.RESET_ALL}")
    if has_python:
        print(f"   {Fore.CYAN}python .claude/skills/symbols/scripts/extract_symbols_python.py{Style.RESET_ALL}")
    print()

    print(f"{Style.BRIGHT}2. Validate Symbols:{Style.RESET_ALL}")
    print(f"   {Fore.CYAN}python .claude/skills/symbols/scripts/validate_symbols.py{Style.RESET_ALL}")
    print()

    print(f"{Style.BRIGHT}3. Query Symbols:{Style.RESET_ALL}")
    print(f"   {Fore.CYAN}python .claude/skills/symbols/scripts/symbol_tools.py{Style.RESET_ALL}")
    print()

    print(f"{Style.BRIGHT}4. Read Documentation:{Style.RESET_ALL}")
    print(f"   {Fore.CYAN}.claude/skills/symbols/CONFIG_README.md{Style.RESET_ALL}")
    print()

    print(f"{Style.BRIGHT}For Help:{Style.RESET_ALL}")
    print(f"   {Fore.CYAN}python .claude/skills/symbols/scripts/init_symbols.py --help{Style.RESET_ALL}")
    print()


def main():
    """Main entry point for the wizard."""
    parser = argparse.ArgumentParser(
        description="Interactive symbols configuration wizard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (recommended)
  python init_symbols.py

  # Quick setup with template
  python init_symbols.py --template=react-typescript-fullstack

  # Non-interactive with all options
  python init_symbols.py --template=python-fastapi --name="MyProject" --symbols-dir="ai" --force

  # List available templates
  python init_symbols.py --list

  # Dry run (preview without writing)
  python init_symbols.py --dry-run
        """,
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List available templates and exit",
    )
    parser.add_argument(
        "--template",
        type=str,
        choices=list(TEMPLATES.keys()),
        help="Project template to use",
    )
    parser.add_argument(
        "--name",
        type=str,
        help="Project name",
    )
    parser.add_argument(
        "--symbols-dir",
        type=str,
        help="Symbols directory (default: ai)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output path for configuration file (default: auto-detect)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing configuration without prompting",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview configuration without writing",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick setup with defaults (implies --template if not specified)",
    )

    args = parser.parse_args()

    # List templates and exit
    if args.list:
        list_templates()
        return 0

    # Determine if running in non-interactive mode
    non_interactive = bool(args.template and args.name and args.symbols_dir) or args.quick

    # Quick mode defaults
    if args.quick:
        if not args.template:
            args.template = "react-typescript-fullstack"
        if not args.symbols_dir:
            args.symbols_dir = "ai"
        non_interactive = True

    try:
        # Welcome screen (skip in non-interactive mode)
        if not non_interactive:
            if not show_welcome():
                print_info("Setup cancelled.")
                return 0

        # Template selection
        template_id = select_template(non_interactive, args.template)

        # Load template
        template_config = load_template(template_id)

        # Project customization
        project_name, symbols_dir = customize_project(
            template_id,
            non_interactive,
            args.name,
            args.symbols_dir,
        )

        # Replace placeholders
        config = replace_placeholders(template_config, project_name, symbols_dir)

        # Preview configuration (skip in quick mode)
        if not args.quick:
            preview_configuration(config)

            if not non_interactive:
                print()
                if not prompt_yes_no("Proceed with this configuration?", default=True):
                    print_info("Setup cancelled.")
                    return 0

        # Determine output path
        if args.output:
            output_path = args.output
        else:
            # Default to .claude/skills/symbols/symbols.config.json
            project_root = find_project_root()
            output_path = project_root / ".claude" / "skills" / "symbols" / "symbols.config.json"

        # Write configuration
        success = write_configuration(
            config,
            output_path,
            dry_run=args.dry_run,
            force=args.force,
        )

        if success and not args.dry_run:
            show_next_steps(config, output_path)
            return 0
        elif success:
            return 0
        else:
            return 1

    except KeyboardInterrupt:
        print()
        print_info("Setup cancelled by user.")
        return 130
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        if "--debug" in sys.argv:
            raise
        return 1


if __name__ == "__main__":
    sys.exit(main())
