TARGET_DIR=/tmp/golden_dict_media
rm -rf ${TARGET_DIR}
mkdir ${TARGET_DIR}
cp golden_dict_media/AddonInitializer.py golden_dict_media/__init__.py ${TARGET_DIR}
pushd ${TARGET_DIR} || exit
zip -r ../golden_dict_media.ankiaddon *
rm -rf ${TARGET_DIR:?}/*
mv ../golden_dict_media.ankiaddon ${TARGET_DIR}

echo "The addon has been packaged to ${TARGET_DIR}/golden_dict_media.ankiaddon"
popd || exit
