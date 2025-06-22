# Version Management

[← Back to README](../../README.md)

## Automated Semantic Release

This project uses [Python Semantic Release](https://python-semantic-release.readthedocs.io/) to automatically manage versioning based on conventional commit messages.

## How It Works

### Commit Message Format

The project follows [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Version Bump Rules

- **Major version bump** (1.0.0 → 2.0.0): Breaking changes with `BREAKING CHANGE:` in footer
- **Minor version bump** (1.0.0 → 1.1.0): New features with `feat:` prefix
- **Patch version bump** (1.0.0 → 1.0.1): Bug fixes with `fix:` or `perf:` prefix

### Supported Commit Types

- `feat:` - New features (minor version bump)
- `fix:` - Bug fixes (patch version bump)  
- `perf:` - Performance improvements (patch version bump)
- `docs:` - Documentation changes (no version bump)
- `style:` - Code style changes (no version bump)
- `refactor:` - Code refactoring (no version bump)
- `test:` - Test changes (no version bump)
- `build:` - Build system changes (no version bump)
- `ci:` - CI configuration changes (no version bump)
- `chore:` - Other changes (no version bump)

## Automated Updates

When a new version is released, the following files are automatically updated:

1. **`pyproject.toml`** - Project version
2. **`README.md`** - Version badge
3. **`CLAUDE.md`** - Project status version references
4. **`CHANGELOG.md`** - Generated with commit history

## Manual Version Management

### Dry Run (Check What Would Happen)

```bash
poetry run semantic-release version --dry-run
```

### Create Version and Tag

```bash
poetry run semantic-release version
```

### Generate Changelog Only

```bash
poetry run semantic-release changelog
```

## GitHub Actions Integration

The project includes a GitHub Actions workflow (`.github/workflows/release.yml`) that:

1. **Triggers on push to main** - Automatically checks for new version
2. **Runs tests** - Ensures code quality before release
3. **Creates GitHub release** - With automatically generated release notes
4. **Updates version badges** - Keeps README current

### GitHub Token

The workflow uses GitHub's built-in `GITHUB_TOKEN` which is automatically provided to GitHub Actions. No additional setup required.

**Note**: If you need advanced features, you can optionally set up a Personal Access Token as `GH_TOKEN` secret for enhanced permissions.

## Cloud Build Integration

To integrate with the existing Cloud Build workflow, you can:

1. **Trigger Cloud Build on new tags** - Configure Cloud Build triggers for version tags
2. **Use semantic version in Docker tags** - Replace `BUILD_ID` with semantic version in `cloudbuild.yaml`

## Examples

### Feature Release (Minor Version Bump)

```bash
git commit -m "feat: add user session management API endpoint"
# Results in: 0.2.0 → 0.3.0
```

### Bug Fix (Patch Version Bump)

```bash
git commit -m "fix: resolve OAuth token refresh issue"
# Results in: 0.2.0 → 0.2.1
```

### Breaking Change (Major Version Bump)

```bash
git commit -m "feat: redesign API authentication

BREAKING CHANGE: OAuth flow now requires additional scope parameter"
# Results in: 0.2.0 → 1.0.0
```

### Documentation Update (No Version Bump)

```bash
git commit -m "docs: update installation guide with new prerequisites"
# Results in: No version change
```

## Benefits

- **Consistent versioning** - No manual version number management
- **Automatic changelog** - Generated from commit messages
- **GitHub integration** - Automatic releases and release notes
- **Badge updates** - Version badges stay current automatically
- **Conventional commits** - Encourages clear, structured commit messages

## Best Practices

1. **Write clear commit messages** - Follow conventional commit format
2. **Use appropriate commit types** - Choose the right prefix for the change
3. **Include breaking changes** - Use `BREAKING CHANGE:` footer when needed
4. **Review dry runs** - Check version changes before committing
5. **Keep commits atomic** - One logical change per commit

For more information, see the [Python Semantic Release documentation](https://python-semantic-release.readthedocs.io/).