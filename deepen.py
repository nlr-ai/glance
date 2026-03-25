"""Multi-resolution graph analysis — recursive space deepening.

Each space node in a graph can be re-analyzed by cropping the image
to its bbox and running analyze_ga_image on the crop. This produces
a child graph linked to the parent, increasing the resolution.

Resolution = log2(total_nodes / root_nodes)

See GLANCE_Mathematics.md §9i for formal definition.
"""

import io
import os
import math
import logging
import yaml

logger = logging.getLogger("deepen")
BASE = os.path.dirname(__file__)


def _get_image_path(ga_image_id):
    """Resolve the filesystem path for a GA image from the database."""
    from db import get_image_by_id
    image = get_image_by_id(ga_image_id)
    if not image:
        return None, None
    filename = image["filename"]
    return os.path.join(BASE, "ga_library", filename), filename


def _crop_to_bbox(image_path, bbox):
    """Crop an image to a normalized [x, y, w, h] bounding box.

    Args:
        image_path: path to the full GA image
        bbox: [x, y, w, h] normalized 0-1

    Returns:
        bytes (PNG), or None if crop fails
    """
    from PIL import Image

    img = Image.open(image_path)
    w, h = img.size
    x, y, bw, bh = bbox

    # Convert normalized coords to pixel coords
    crop_box = (
        int(x * w),
        int(y * h),
        int((x + bw) * w),
        int((y + bh) * h),
    )

    # Clamp to image bounds
    crop_box = (
        max(0, crop_box[0]),
        max(0, crop_box[1]),
        min(w, crop_box[2]),
        min(h, crop_box[3]),
    )

    # Skip if crop is too small (< 20px in either dimension)
    if (crop_box[2] - crop_box[0]) < 20 or (crop_box[3] - crop_box[1]) < 20:
        logger.warning(f"Crop too small: {crop_box} — skipping")
        return None

    cropped = img.crop(crop_box)
    buf = io.BytesIO()
    cropped.save(buf, format="PNG")
    return buf.getvalue()


def _transform_bbox(child_bbox, parent_bbox):
    """Transform child bbox coords (relative to crop) to absolute coords.

    Child bbox is relative to the cropped space.
    Parent bbox: [sx, sy, sw, sh] in absolute (normalized 0-1) coords.

    Returns: [abs_x, abs_y, abs_w, abs_h] in absolute coords.
    """
    sx, sy, sw, sh = parent_bbox
    cx, cy, cw, ch = child_bbox
    return [
        sx + cx * sw,
        sy + cy * sh,
        cw * sw,
        ch * sh,
    ]


def _namespace_id(parent_space_id, child_id):
    """Prefix child node ID with parent space ID to avoid collisions.

    e.g. "space:header" + "thing:icon_1" -> "space:header:thing:icon_1"
    """
    return f"{parent_space_id}:{child_id}"


def _merge_child_graph(parent_graph, child_graph, parent_space_id, parent_bbox, depth):
    """Merge a child graph into the parent graph.

    - Namespace child IDs
    - Transform child bbox to absolute coords
    - Add containment links from child nodes to parent space
    - Tag child nodes with resolution_depth
    - Deduplicate against existing nodes

    Mutates parent_graph in place.
    """
    existing_ids = {n["id"] for n in parent_graph.get("nodes", [])}
    existing_link_pairs = {
        (l.get("source", ""), l.get("target", ""))
        for l in parent_graph.get("links", [])
    }

    child_nodes = child_graph.get("nodes", [])
    child_links = child_graph.get("links", [])

    # Build ID mapping: old child ID -> new namespaced ID
    id_map = {}
    for node in child_nodes:
        old_id = node["id"]
        new_id = _namespace_id(parent_space_id, old_id)
        id_map[old_id] = new_id

    # Add child nodes
    for node in child_nodes:
        new_id = id_map[node["id"]]

        # Skip if already exists (deduplication)
        if new_id in existing_ids:
            continue

        node["id"] = new_id
        node["resolution_depth"] = depth

        # Transform bbox if present
        bbox = node.get("bbox")
        if bbox and isinstance(bbox, list) and len(bbox) == 4:
            try:
                child_bbox = [float(v) for v in bbox]
                node["bbox"] = _transform_bbox(child_bbox, parent_bbox)
            except (ValueError, TypeError):
                pass

        parent_graph["nodes"].append(node)
        existing_ids.add(new_id)

        # Add containment link: child -> parent space
        link_pair = (new_id, parent_space_id)
        if link_pair not in existing_link_pairs:
            parent_graph["links"].append({
                "source": new_id,
                "target": parent_space_id,
                "link_type": "containment",
                "weight": 1.0,
            })
            existing_link_pairs.add(link_pair)

    # Add child links (with remapped IDs)
    for link in child_links:
        old_src = link.get("source", "")
        old_tgt = link.get("target", "")
        new_src = id_map.get(old_src, old_src)
        new_tgt = id_map.get(old_tgt, old_tgt)

        link_pair = (new_src, new_tgt)
        if link_pair in existing_link_pairs:
            continue

        # Only add links where both endpoints exist
        if new_src in existing_ids and new_tgt in existing_ids:
            parent_graph["links"].append({
                "source": new_src,
                "target": new_tgt,
                "link_type": link.get("link_type", "link"),
                "weight": link.get("weight", 0.5),
            })
            existing_link_pairs.add(link_pair)


def deepen(ga_image_id, max_depth=1, image_path=None):
    """Recursively analyze spaces within a GA graph.

    For each space at current max depth:
    1. Crop the GA image to the space's bbox
    2. Run analyze_ga_image on the crop (with prior_graph context)
    3. Transform child node bbox coords to absolute (parent space coords)
    4. Namespace child node IDs: thing:s3:detail_1
    5. Link child nodes to parent space (containment)
    6. Tag child nodes with resolution_depth
    7. Merge child graph into parent graph
    8. save_graph the merged result

    Args:
        ga_image_id: GA image ID in database
        max_depth: how many levels to recurse (1 = analyze each space once)
        image_path: path to GA image (auto-detected from DB if None)

    Returns:
        dict with stats: {depth, total_nodes, total_links, spaces_deepened,
                         resolution, graph_id}
    """
    from db import get_latest_graph, save_graph
    from vision_scorer import analyze_ga_image

    # Resolve image path
    if not image_path:
        image_path, filename = _get_image_path(ga_image_id)
        if not image_path or not os.path.exists(image_path):
            raise FileNotFoundError(
                f"GA image not found for id={ga_image_id}"
            )
    else:
        filename = os.path.basename(image_path)

    # Get the latest graph
    latest = get_latest_graph(ga_image_id)
    if not latest:
        raise ValueError(
            f"No graph found for ga_image_id={ga_image_id} — run vision analysis first"
        )

    graph = latest["graph"]
    root_node_count = len(graph.get("nodes", []))

    # Tag existing root nodes with resolution_depth=0 if not already tagged
    for node in graph.get("nodes", []):
        if "resolution_depth" not in node:
            node["resolution_depth"] = 0

    spaces_deepened = 0

    for current_depth in range(max_depth):
        target_depth = current_depth  # spaces at this depth get deepened

        # Find spaces at the current target depth that have valid bboxes
        spaces_to_deepen = [
            n for n in graph.get("nodes", [])
            if n.get("node_type") == "space"
            and n.get("resolution_depth", 0) == target_depth
            and n.get("bbox")
            and isinstance(n.get("bbox"), list)
            and len(n.get("bbox", [])) == 4
        ]

        if not spaces_to_deepen:
            logger.info(f"No spaces with bbox at depth {target_depth} — stopping")
            break

        for space in spaces_to_deepen:
            space_id = space["id"]
            bbox = space["bbox"]

            try:
                bbox_floats = [float(v) for v in bbox]
            except (ValueError, TypeError):
                logger.warning(f"Invalid bbox for {space_id}: {bbox} — skipping")
                continue

            # Validate bbox is reasonable
            if bbox_floats[2] <= 0 or bbox_floats[3] <= 0:
                logger.warning(f"Zero-area bbox for {space_id} — skipping")
                continue

            # Crop the image
            crop_bytes = _crop_to_bbox(image_path, bbox_floats)
            if not crop_bytes:
                logger.warning(f"Failed to crop for {space_id} — skipping")
                continue

            # Build prior context: the parent space info
            prior_context = {
                "parent_space": {
                    "id": space_id,
                    "name": space.get("name", ""),
                    "synthesis": space.get("synthesis", ""),
                },
            }

            # Run vision analysis on the crop
            try:
                logger.info(f"Deepening space '{space.get('name', space_id)}' "
                           f"(depth {current_depth} -> {current_depth + 1})")
                result = analyze_ga_image(
                    crop_bytes,
                    filename=f"crop_{space_id}_{filename}",
                    prior_graph=prior_context,
                )
                child_graph = result["graph"]
            except Exception as e:
                logger.error(f"Vision analysis failed for {space_id}: {e}")
                continue

            # Merge child graph into parent
            _merge_child_graph(
                graph, child_graph, space_id, bbox_floats,
                depth=current_depth + 1,
            )
            spaces_deepened += 1
            logger.info(
                f"Merged {len(child_graph.get('nodes', []))} child nodes "
                f"from {space_id}"
            )

    # Calculate resolution metric
    total_nodes = len(graph.get("nodes", []))
    total_links = len(graph.get("links", []))
    resolution = (
        math.log2(total_nodes / root_node_count)
        if root_node_count > 0 and total_nodes > root_node_count
        else 0.0
    )

    # Save the merged graph (skip_deepen=True to prevent infinite recursion)
    graph_id = save_graph(
        graph,
        ga_image_id=ga_image_id,
        graph_type="deepened",
        source="deepen",
        version=f"depth_{max_depth}",
        skip_deepen=True,
    )

    stats = {
        "depth": max_depth,
        "total_nodes": total_nodes,
        "total_links": total_links,
        "root_nodes": root_node_count,
        "spaces_deepened": spaces_deepened,
        "resolution": round(resolution, 2),
        "graph_id": graph_id,
    }

    logger.info(
        f"Deepen complete: {spaces_deepened} spaces deepened, "
        f"{root_node_count} -> {total_nodes} nodes, "
        f"resolution={resolution:.2f}"
    )

    return stats
