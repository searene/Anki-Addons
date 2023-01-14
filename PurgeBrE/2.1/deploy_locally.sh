TARGET_FOLDER="/Users/joeygreen/Library/Application Support/Anki2/addons21/purge_bre"
rm -rf "${TARGET_FOLDER}"
mkdir -p "${TARGET_FOLDER}"
rsync -av --progress purge_bre/* "${TARGET_FOLDER}" --exclude __pycache__