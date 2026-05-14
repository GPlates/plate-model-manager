import argparse
import json
import logging
import os
import sys

from plate_model_manager import PlateModelManager, __version__, check_update

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
