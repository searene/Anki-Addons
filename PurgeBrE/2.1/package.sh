TARGET_DIR=/tmp/purge_bre
rm -rf ${TARGET_DIR}
mkdir ${TARGET_DIR}
cp purgeBrE/AddonInitializer.py purge_bre/__init__.py ${TARGET_DIR}
pushd ${TARGET_DIR} || exit
zip -r ../purge_bre.ankiaddon *
rm -rf ${TARGET_DIR:?}/*
mv ../purge_bre.ankiaddon ${TARGET_DIR}

echo "The addon has been packaged to ${TARGET_DIR}/purge_bre.ankiaddon"
popd || exit
