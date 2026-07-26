#!/bin/bash
set -euo pipefail

repository="aston76/lending-pro-freeware"
application_name="Lending Pro Freeware.app"
asset_name="Lending-Pro-Freeware-macOS-arm64.dmg"
checksum_name="${asset_name}.sha256"
release_url="https://github.com/${repository}/releases/latest/download"
install_directory="${LENDING_PRO_INSTALL_DIR:-${HOME}/Applications}"
temporary_directory="$(mktemp -d -t lending-pro-install)"
mount_directory="${temporary_directory}/mount"
mounted="false"

cleanup() {
    if [[ "${mounted}" == "true" ]]; then
        hdiutil detach "${mount_directory}" -quiet || true
    fi
    rm -rf "${temporary_directory}"
}
trap cleanup EXIT INT TERM

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "Lending Pro Freeware can only be installed by this script on macOS." >&2
    exit 1
fi

if [[ "$(uname -m)" != "arm64" ]]; then
    echo "This release requires an Apple Silicon Mac (M1 or newer)." >&2
    exit 1
fi

for command_name in curl hdiutil shasum ditto; do
    if ! command -v "${command_name}" >/dev/null 2>&1; then
        echo "Required command not found: ${command_name}" >&2
        exit 1
    fi
done

mkdir -p "${mount_directory}" "${install_directory}"
echo "Downloading Lending Pro Freeware..."
curl --fail --location --silent --show-error \
    "${release_url}/${asset_name}" \
    --output "${temporary_directory}/${asset_name}"
curl --fail --location --silent --show-error \
    "${release_url}/${checksum_name}" \
    --output "${temporary_directory}/${checksum_name}"

expected_checksum="$(awk 'NR == 1 { print $1 }' "${temporary_directory}/${checksum_name}")"
actual_checksum="$(shasum -a 256 "${temporary_directory}/${asset_name}" | awk '{ print $1 }')"
if [[ -z "${expected_checksum}" || "${actual_checksum}" != "${expected_checksum}" ]]; then
    echo "Download verification failed. The application was not installed." >&2
    exit 1
fi

echo "Checksum verified. Installing..."
hdiutil attach "${temporary_directory}/${asset_name}" \
    -readonly -nobrowse -mountpoint "${mount_directory}" -quiet
mounted="true"

source_application="${mount_directory}/${application_name}"
target_application="${install_directory}/${application_name}"
if [[ ! -d "${source_application}" ]]; then
    echo "The application was not found in the downloaded image." >&2
    exit 1
fi

if [[ -e "${target_application}" ]]; then
    backup_application="${install_directory}/Lending Pro Freeware.backup-$(date +%Y%m%d-%H%M%S).app"
    mv "${target_application}" "${backup_application}"
    echo "Previous version preserved at: ${backup_application}"
fi

ditto "${source_application}" "${target_application}"
codesign --verify --deep --strict "${target_application}"

echo "Installed successfully: ${target_application}"
echo "Open it from Finder or run: open \"${target_application}\""
echo "On first launch, macOS may require Control-click > Open because the app is not notarized."
