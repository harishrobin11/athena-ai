from ..multimodal.image_service import analyze_image


def execute(
    tool_input,
    context,
):
    """
    Analyze uploaded image.

    Context supports:
        image_path  -> single image
        image_paths -> multiple images (latest image is used)
    """

    image_paths = context.get("image_paths")

    if image_paths:
        image_path = image_paths[-1]

        result = analyze_image(
            image_path=image_path,
            prompt=tool_input,
        )

        print("\n" + "=" * 70)
        print("IMAGE TOOL RESULT")
        print(type(result))
        print(repr(result))
        print("=" * 70)

        return result

    image_path = context.get("image_path")

    if image_path:
        result = analyze_image(
            image_path=image_path,
            prompt=tool_input,
        )

        print("\n" + "=" * 70)
        print("IMAGE TOOL RESULT")
        print(type(result))
        print(repr(result))
        print("=" * 70)

        return result

    raise ValueError("No image supplied.")