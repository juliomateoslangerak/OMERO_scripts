import marimo

__generated_with = "0.18.4"

app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import numpy as np

    import analysis_functions
    import omero_toolbox as omero_tb

    return analysis_functions, mo, np, omero_tb


@app.cell
def _(mo):
    analysis_form = (
        mo.md(
            """Fill the analysis parameters:
        
        {connection_parameters}
        {data_parameters}
        """
        )
        .batch(
            connection_parameters=mo.ui.dictionary(
                label="Connection parameters",
                elements={
                    "omero_username": mo.ui.text(label="OMERO username"),
                    "omero_password": mo.ui.text(
                        label="OMERO password",
                        kind="password",
                    ),
                    "omero_host": mo.ui.text(
                        value="omero.mri.cnrs.fr",
                        label="OMERO server URL",
                    ),
                    "omero_port": mo.ui.number(
                        value=4064,
                        start=1,
                        step=1,
                        label="OMERO port",
                    ),
                    "omero_group": mo.ui.text(value="Dorade project", label="Group"),
                    "connection_secured": mo.ui.checkbox(
                        value=True,
                        label="Secured connection",
                    ),
                },
            ),
            data_parameters=mo.ui.dictionary(
                label="Data parameters",
                elements={
                    "dataset_id": mo.ui.number(start=1, step=1, label="Dataset ID"),
                    "image_name_include_filter": mo.ui.text(
                        value="_cmle.ics",
                        label="Image name include filter",
                    ),
                    "image_name_exclude_filter": mo.ui.text(
                        value="_MRG",
                        label="Image name exclude filter",
                    ),
                    "delete_preexisting_merges": mo.ui.checkbox(
                        value=False,
                        label="Delete preexisting merges (use with caution)",
                    ),
                    "ch_a": mo.ui.number(
                        value=1,
                        label="Channel a (first channel is 0)",
                        step=1,
                    ),
                    "ch_b": mo.ui.number(
                        value=3,
                        label="Channel b (first channel is 0)",
                        step=1,
                    ),
                    "rescale_channels": mo.ui.checkbox(
                        value=True,
                        label="Rescale source images",
                    ),
                    "rescale_cha_min": mo.ui.number(
                        value=0,
                        label="Rescale channel a min",
                        step=1,
                    ),
                    "rescale_cha_max": mo.ui.number(
                        value=10000,
                        label="Rescale channel a max",
                        step=1,
                    ),
                    "rescale_chb_min": mo.ui.number(
                        value=0,
                        label="Rescale channel b min",
                        step=1,
                    ),
                    "rescale_chb_max": mo.ui.number(
                        value=10000,
                        label="Rescale channel b max",
                        step=1,
                    ),
                },
            ),
        )
        .form()
    )

    analysis_form


@app.cell
def _(
    mo,
    analysis_functions,
    np,
    omero_tb,
    analysis_form,
):
    if analysis_form.value is None:
        mo.md("### Waiting for input.")

    else:
        conn_params = analysis_form.value["connection_parameters"]
        data_params = analysis_form.value["data_parameters"]

        with mo.status.spinner(title="Connecting to OMERO...") as _spinner:
            conn = omero_tb.open_connection(
                username=conn_params["omero_username"],
                password=conn_params["omero_password"],
                host=conn_params["omero_host"],
                port=conn_params["omero_port"],
                group=conn_params["omero_group"],
                secure=conn_params["connection_secured"],
            )

            if conn.connect():
                _spinner.update("Connected to OMERO.")
            else:
                _spinner.update("Failed to connect to OMERO.")
                raise Exception("Connection failed")

            try:
                dataset = omero_tb.get_dataset(
                    connection=conn, dataset_id=data_params["dataset_id"]
                )
                dataset_images = omero_tb.get_dataset_images(dataset=dataset)

                for image in dataset_images:
                    image_name = image.getName()
                    _spinner.update(f"Analyzing: {image_name}")
                    if not data_params["image_name_include_filter"] in image_name:
                        continue
                    if data_params["image_name_exclude_filter"] in image_name:
                        if data_params["delete_preexisting_merges"]:
                            omero_tb.delete_image(conn, image)
                        continue

                    raw_image_data = omero_tb.get_intensities(image)  # zctyx

                    merged_channel = analysis_functions.merge_channels(
                        raw_image_data[:, data_params["ch_a"],...],
                        raw_image_data[:, data_params["ch_b"],...],
                        range_a=(data_params["rescale_cha_min"], data_params["rescale_cha_max"]),
                        range_b=(data_params["rescale_chb_min"], data_params["rescale_chb_max"]),
                        rescale=data_params["rescale_channels"]
                    )

                    merged_image_data = np.concat(raw_image_data, merged_channel, axis=1)

                    omero_tb.create_image_from_numpy_array(
                        connection=conn,
                        data=merged_image_data,
                        image_name=f"{image_name.split('.')[:-1]}_THR",
                        dataset=dataset,
                        source_image_id=image.getId(),
                        # channels_list=[analysis_params["channel"]],
                    )

                _spinner.update("✅ **Analysis Complete!**")

            except Exception as e:
                _spinner.update(f"❌ **Error**: {str(e)}")
                raise e

            finally:
                conn.close()


if __name__ == "__main__":
    app.run()
