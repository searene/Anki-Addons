TARGET_FOLDER="/Users/joeygreen/Library/Application Support/Anki2/addons21/my_custom_logic"
rm -rf "${TARGET_FOLDER}"
mkdir -p "${TARGET_FOLDER}"
rsync -av --progress my_custom_logic/* "${TARGET_FOLDER}" --exclude __pycache__
