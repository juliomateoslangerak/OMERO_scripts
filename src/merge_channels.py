import numpy as np
import getpass

import analysis_functions
import omero_toolbox as omero_tb

def run(
        conn,
        dataset_id: int,
        ch_a: int,
        ch_b: int,
        rescale_channels: bool,
        rescale_ch_a_min: int,
        rescale_ch_a_max: int,
        rescale_ch_b_min: int,
        rescale_ch_b_max: int,
        image_name_include_filter: str,
        image_name_exclude_filter: str,
        delete_preexisting_merges: bool,
):
    try:
        dataset = omero_tb.get_dataset(
            connection=conn, dataset_id=dataset_id
        )
        dataset_images = omero_tb.get_dataset_images(dataset=dataset)

        for image in dataset_images:
            image_name = image.getName()
            print(f"Analyzing: {image_name}")
            if image_name_include_filter not in image_name:
                continue
            if image_name_exclude_filter in image_name:
                if delete_preexisting_merges:
                    omero_tb.delete_image(conn, image)
                continue

            raw_image_data = omero_tb.get_intensities(image)  # zctyx
            new_channels_list = list(range(raw_image_data.shape[1]))
            new_channels_list.append(ch_a)

            merged_channel = analysis_functions.merge_channels(
                raw_image_data[:, ch_a, ...],
                raw_image_data[:, ch_b, ...],
                range_a=(rescale_ch_a_min, rescale_ch_a_max),
                range_b=(rescale_ch_b_min, rescale_ch_b_max),
                rescale=rescale_channels,
            )
            merged_channel = np.expand_dims(merged_channel, axis=1)

            # delete channels to merge and insert merged channel
            merged_image_data = np.concatenate([raw_image_data, merged_channel], axis=1)


            merged_image = omero_tb.create_image_from_numpy_array(
                connection=conn,
                data=merged_image_data,
                image_name=f"{".".join(image_name.split('.')[:-1])}_MRG",
                dataset=dataset,
                source_image_id=image.getId(),
                channels_list=new_channels_list,
            )

        print("✅ **Analysis Complete!**")

    except Exception as e:
        raise e

    finally:
        conn.close()


if __name__ == "__main__":
    user_name = input("Enter your username: ")
    password = getpass.getpass("Enter your password: ")
    host = input("Enter the OMERO server address: ") or "omero.mri.cnrs.fr"
    port = input("Enter the OMERO server port: ") or "4064"
    group = input("Enter the OMERO group name: ")
    dataset_id = int(input("Enter the dataset ID: "))
    ch_a = int(input("Enter the channel A (first channel is 0): "))
    ch_b = int(input("Enter the channel B (first channel is 0): "))
    delete_preexisting_merges = input("Delete preexisting merges? (y/n): ") or "n"
    delete_preexisting_merges = delete_preexisting_merges.lower() == "y"
    rescale_channels = input("Rescale channels? (y/n): ") or "n"
    rescale_channels = rescale_channels.lower() == "y"
    if rescale_channels:
        rescale_ch_a_min = int(input("Enter the minimum value for channel A: ")) or 0
        rescale_ch_a_max = int(input("Enter the maximum value for channel A: "))
        rescale_ch_b_min = int(input("Enter the minimum value for channel B: ")) or 0
        rescale_ch_b_max = int(input("Enter the maximum value for channel B: "))
    else:
        rescale_ch_a_min = None
        rescale_ch_a_max = None
        rescale_ch_b_min = None
        rescale_ch_b_max = None

    image_name_include_filter = input("Enter the image name include filter: ")
    image_name_exclude_filter = input("Enter the image name exclude filter: ")


    conn = omero_tb.open_connection(
        username=user_name,
        password=password,
        host=host,
        port=int(port),
        group=group,
        secure=True,
    )

    run(
        conn=conn,
        dataset_id=dataset_id,
        ch_a=ch_a,
        ch_b=ch_b,
        rescale_channels=rescale_channels,
        rescale_ch_a_min=int(rescale_ch_a_min),
        rescale_ch_a_max=int(rescale_ch_a_max),
        rescale_ch_b_min=int(rescale_ch_b_min),
        rescale_ch_b_max=int(rescale_ch_b_max),
        image_name_include_filter=image_name_include_filter,
        image_name_exclude_filter=image_name_exclude_filter,
        delete_preexisting_merges=delete_preexisting_merges,
    )
