#
#    Copyright (C) 2024-2026 The University of Sydney, Australia
#
#    This program is free software; you can redistribute it and/or modify it under
#    the terms of the GNU General Public License, version 2, as published by
#    the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful, but WITHOUT
#    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#    FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
#    for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
import argparse
import json
import logging
import os
import sys

from plate_model_manager import PlateModelManager, __version__, check_update
from plate_model_manager.utils import collect_update_model
from plate_model_manager.utils.layer_validation import validate_layers_source

logger = logging.getLogger("pmm")


class ArgParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write(f"error: {message}\n")
        self.print_help()
        sys.exit(1)


def _run_ls_command(args):
    if args.repository == None:
        pm_manager = PlateModelManager()
    else:
        pm_manager = PlateModelManager(args.repository)

    if args.model:
        model = pm_manager.get_model(args.model)
        if model:
            print(json.dumps(model.get_cfg(), indent=2))
        else:
            print(f"No such model {args.model}")
    else:
        for name in pm_manager.get_available_model_names():
            print(name)


def _run_download_command(args):
    logger.info(f"Downloading {args.model}")
    if args.repository == None:
        pm_manager = PlateModelManager()
    else:
        pm_manager = PlateModelManager(args.repository)

    if args.model.lower() == "all":
        pm_manager.download_all_models(args.path)
        logger.info(f"All models have been saved in {args.path}.")
    else:
        model = pm_manager.get_model(args.model)
        if model is not None:
            model.set_data_dir(args.path)
            # print(args.download_rasters)
            if args.download_rasters:
                model.download_all()
            else:
                model.download_all_layers()
            logger.info(f"Model({args.model}) has been saved in {model.model_dir}.")


def _run_check_update_command(args):
    check_update()


def _run_validate_layers_command(args):
    checked_models, issues, base_url = validate_layers_source(
        args.config_url,
        base_url=args.base_url,
        timeout=args.timeout,
    )

    if issues:
        print("Layer validation failed:")
        for issue in issues:
            print(f"- {issue}")
        raise SystemExit(1)

    print(f"Layer validation passed for {checked_models} models against {base_url}.")


def _run_collect_models_command(args):
    try:
        collect_update_model.collect_model_files(
            args.model,
            args.target_dir,
            args.source,
            upload=args.upload,
            upload_target=args.upload_target,
            identity_file=args.identity_file,
            remote_path=args.remote_path,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc


def main():
    parser = ArgParser()

    parser.add_argument("-v", "--version", action="store_true")

    subparser = parser.add_subparsers(dest="command")

    ls_cmd = subparser.add_parser(
        "ls",
        description="List all available plate model names. If given a model name, show the details of the model.",
        help="list all available plate model names. if given a model name, show the details of the model.",
    )
    ls_cmd.add_argument(
        "-r",
        "--repository",
        type=str,
        dest="repository",
        help="indicate which repository to use. you don't need this argument in most situations.",
    )
    ls_cmd.add_argument(
        "model",
        type=str,
        nargs="?",
        help="the model name. If given, show the details of the model.",
    )
    ls_cmd.set_defaults(func=_run_ls_command)

    download_cmd = subparser.add_parser(
        "download",
        description="Download a plate model or all plate models.",
        help="download a plate model or all plate models",
    )
    download_cmd.add_argument(
        "model", type=str, help="the model name. use 'all' to download all models."
    )
    download_cmd.add_argument(
        "path",
        type=str,
        nargs="?",
        default=os.getcwd(),
        help="the location to save the plate model files. use the current working directory by default.",
    )
    download_cmd.add_argument(
        "-r",
        "--repository",
        type=str,
        dest="repository",
        help="indicate which repository to use. you don't need this argument in most situations.",
    )
    download_cmd.add_argument(
        "--download-rasters",
        action="store_true",
        help="a flag to indicate if download raster files. the raster files may be large in size.",
    )
    download_cmd.set_defaults(func=_run_download_command)

    check_update_cmd = subparser.add_parser(
        "check-update",
        description="Check if new versions of plate models are available on Zenodo.",
        help="check if new versions of plate models are available on Zenodo",
    )
    check_update_cmd.set_defaults(func=_run_check_update_command)

    validate_layers_cmd = subparser.add_parser(
        "validate-layers",
        description="Validate configured Layers against remote model zip files.",
        help="validate configured layers against remote model zip files",
    )
    validate_layers_cmd.add_argument(
        "--config-url",
        default="https://repo.gplates.org/webdav/pmm/config/models_v2.json",
        help="URL or local path to a models config JSON file. Defaults to pmm config/models_v2.json.",
    )
    validate_layers_cmd.add_argument(
        "--base-url",
        default="https://repo.gplates.org/webdav/pmm",
        help="Base URL of remote model folders to validate against.",
    )
    validate_layers_cmd.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="HTTP timeout in seconds for remote requests.",
    )
    validate_layers_cmd.set_defaults(func=_run_validate_layers_command)

    collect_models_cmd = subparser.add_parser(
        "collect-models",
        description=(
            "Collect source model files from configured metadata and optionally upload "
            "generated archives."
        ),
        help="collect source model files and optionally upload generated archives",
    )
    collect_models_cmd.add_argument(
        "model",
        type=str,
        help="model name to collect, or 'all' to process all configured models.",
    )
    collect_models_cmd.add_argument(
        "target_dir",
        type=str,
        nargs="?",
        default=".",
        help="base directory where model folders are created.",
    )
    collect_models_cmd.add_argument(
        "--source",
        default=str(collect_update_model.DEFAULT_COLLECT_MODELS_SOURCE),
        help="path or URL to model source configuration JSON.",
    )
    collect_models_cmd.add_argument(
        "--upload",
        action="store_true",
        help="upload generated model files after collection.",
    )
    collect_models_cmd.add_argument(
        "--upload-target",
        default=collect_update_model.DEFAULT_UPLOAD_TARGET,
        help="SSH destination in the form user@host.",
    )
    collect_models_cmd.add_argument(
        "--identity-file",
        default=collect_update_model.DEFAULT_IDENTITY_FILE,
        help="SSH private key path for upload.",
    )
    collect_models_cmd.add_argument(
        "--remote-path",
        default=None,
        help=(
            "Remote path for upload. For single model runs, defaults to "
            "<DEFAULT_REMOTE_PATH>/<model>."
        ),
    )
    collect_models_cmd.set_defaults(func=_run_collect_models_command)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(0)

    args = parser.parse_args()

    if args.version:
        print(__version__)
        return

    args.func(args)


if __name__ == "__main__":
    main()
