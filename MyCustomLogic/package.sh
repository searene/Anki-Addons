TARGET_DIR=/tmp/my_custom_logic
rm -rf ${TARGET_DIR}
mkdir ${TARGET_DIR}
rsync -av --progress my_custom_logic ${TARGET_DIR} --exclude __pycache__
pushd ${TARGET_DIR} || exit
zip -r ../my_custom_logic.ankiaddon *
rm -rf ${TARGET_DIR:?}/*
mv ../my_custom_logic.ankiaddon ${TARGET_DIR}

echo "The addon has been packaged to ${TARGET_DIR}/my_custom_logic.ankiaddon"
popd || exit
