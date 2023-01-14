TARGET_DIR=/tmp/golden_dict_media
rm -rf ${TARGET_DIR}
mkdir ${TARGET_DIR}
rsync -av --progress golden_dict_media ${TARGET_DIR} --exclude __pycache__
pushd ${TARGET_DIR} || exit
zip -r ../golden_dict_media.ankiaddon *
rm -rf ${TARGET_DIR:?}/*
mv ../golden_dict_media.ankiaddon ${TARGET_DIR}

echo "The addon has been packaged to ${TARGET_DIR}/golden_dict_media.ankiaddon"
popd || exit
