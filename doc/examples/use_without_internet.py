from plate_model_manager import PlateModel

try:
    model = PlateModelManager().get_model("Zahirovic2022", data_dir="plate-model-repo")
except:
    # if unable to connect to the servers, try to use the local files
    model = PlateModel(
        model_name="Zahirovic2022", data_dir="plate-model-repo", readonly=True
    )
    print("Unable to connect to the servers. Using local files in readonly mode.")

for layer in model.get_avail_layers():
    print(model.get_layer(layer))
