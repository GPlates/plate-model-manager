from joblib import Parallel, delayed
import gplately
from plate_model_manager import PlateModelManager


def worker_task(index, static_polygons_files):
    static_polygons = gplately.gpml.load_feature_collection_from_files(
        static_polygons_files
    )
    print(f"Worker {index} is processing {len(static_polygons)} static polygons.")
    return


static_polygons_files = (
    PlateModelManager().get_model("Zahirovic2022").get_static_polygons()
)

Parallel(n_jobs=4)(
    delayed(worker_task)(idx, static_polygons_files) for idx in range(10)
)
