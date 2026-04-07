import argparse
import sys


def build_parser():
    parser = argparse.ArgumentParser(
        prog="skill_packager",
        description="Skill packager CLI tool",
    )
    subparsers = parser.add_subparsers(dest="command")

    # metadata subcommand
    metadata_parser = subparsers.add_parser("metadata", help="Extract metadata from skill(s)")
    metadata_parser.add_argument("--skill-path", action="append", required=True, help="Path to a skill directory")

    # scaffold subcommand
    scaffold_parser = subparsers.add_parser("scaffold", help="Scaffold files from metadata")
    scaffold_parser.add_argument("--metadata", required=True, help="Path to meta.json")
    scaffold_parser.add_argument("--output", required=True, help="Output directory")

    # build-zip subcommand
    build_zip_parser = subparsers.add_parser("build-zip", help="Build a zip archive for a skill")
    build_zip_parser.add_argument("--skill-dir", required=True, help="Path to skill directory")
    build_zip_parser.add_argument("--output", help="Output path for zip file")
    build_zip_parser.add_argument("--version", help="Version to embed in zip")

    # validate subcommand
    validate_parser = subparsers.add_parser("validate", help="Validate a skill repository")
    validate_parser.add_argument("repo_dir", help="Path to repository directory")
    validate_parser.add_argument("--json", action="store_true", dest="json_output", help="Output results as JSON")

    # bump-version subcommand
    bump_version_parser = subparsers.add_parser("bump-version", help="Bump the version of a skill")
    bump_version_parser.add_argument("repo_dir", help="Path to repository directory")
    bump_version_parser.add_argument("version", help="New version string")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "metadata":
        from skill_packager.metadata import run_metadata
        run_metadata(args)
    elif args.command == "scaffold":
        from skill_packager.scaffold import run_scaffold
        run_scaffold(args)
    elif args.command == "build-zip":
        from skill_packager.build_zip import run_build_zip
        run_build_zip(args)
    elif args.command == "validate":
        from skill_packager.validate import run_validate
        run_validate(args)
    elif args.command == "bump-version":
        from skill_packager.bump_version import run_bump_version
        run_bump_version(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
