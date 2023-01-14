TARGET_FOLDER="/Users/joeygreen/Library/Application Support/Anki2/addons21/GoldenDictMedia"
rm -rf "${TARGET_FOLDER}"
mkdir -p "${TARGET_FOLDER}"
rsync -av --progress golden_dict_media/* "${TARGET_FOLDER}" --exclude __pycache__
