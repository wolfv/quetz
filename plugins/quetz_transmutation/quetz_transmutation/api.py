import json
import logging
import os
import pickle
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from conda_package_handling.api import _convert
from fastapi import APIRouter, Depends

from quetz import authorization
from quetz.condainfo import calculate_file_hashes_and_size
from quetz.dao import Dao
from quetz.deps import get_db, get_rules
from quetz.jobs.models import Job
from quetz.pkgstores import PackageStore

from .rest_models import PackageSpec

router = APIRouter()
logger = logging.getLogger("quetz-cli")


def transmutation(package_version: dict, config, pkgstore: PackageStore, dao: Dao):
    filename: str = package_version["filename"]
    channel: str = package_version["channel_name"]
    package_format: str = package_version["package_format"]
    package_name: str = package_version["package_name"]
    platform = package_version["platform"]
    version = package_version["version"]
    build_number = package_version["build_number"]
    build_string = package_version["build_string"]
    uploader_id = package_version["uploader_id"]
    info = json.loads(package_version["info"])

    if package_format == "tarbz2" or not filename.endswith(".tar.bz2"):
        return

    fh = pkgstore.serve_path(channel, Path(platform) / filename)

    with TemporaryDirectory() as tmpdirname:
        local_file_name = os.path.join(tmpdirname, filename)
        with open(local_file_name, "wb") as local_file:
            # chunk size 10MB
            shutil.copyfileobj(fh, local_file, 10 * 1024 * 1024)

        res = _convert(local_file_name, ".conda", tmpdirname, force=True)
        errors, out_fn = "", ""
        if res is not None:
            fn, out_fn, errors = res

        if res is None or errors:
            logger.error(f"transmutation errors --> {errors}")
            return

        filename_conda = os.path.basename(filename).replace('.tar.bz2', '.conda')

        logger.info(f"Adding file to package store: {Path(platform) / filename_conda}")

        with open(out_fn, 'rb') as f:
            calculate_file_hashes_and_size(info, f)
            f.seek(0)
            pkgstore.add_package(f, channel, f"{platform}/{filename_conda}")

        version = dao.create_version(
            channel,
            package_name,
            "conda",
            platform,
            version,
            build_number,
            build_string,
            filename_conda,
            json.dumps(info),
            uploader_id,
            info["size"],
            upsert=True,
        )

        logger.info(
            f"Created: {filename_conda} with {info['size']} and {info['sha256']}"
        )

        if os.path.exists(out_fn):
            os.remove(out_fn)


transmutation_serialized = pickle.dumps(transmutation)


@router.put("/api/transmutation", tags=["plugins"])
def put_transmutation(
    package_spec: PackageSpec,
    db=Depends(get_db),
    auth: authorization.Rules = Depends(get_rules),
):
    user = auth.get_user()
    job = Job(
        owner_id=user,
        manifest=transmutation_serialized,
        items_spec=package_spec.package_spec,
    )
    db.add(job)
    db.commit()
