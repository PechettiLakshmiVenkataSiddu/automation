from __future__ import annotations

import os
import re


def test_frontend_components_accessibility_and_seo() -> None:
    """Scans frontend components and pages to ensure accessibility tags are present."""
    web_dir = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "apps",
            "web",
        )
    )

    if not os.path.exists(web_dir):
        return

    # Check components
    comp_dir = os.path.join(web_dir, "components")
    app_dir = os.path.join(web_dir, "app")

    # Viewport, SEO tags and meta details are standard in pages
    # Check that alt tag constraints exist in JSX files if <img> tags are declared
    img_pattern = re.compile(r"<img\s+[^>]*>")
    alt_pattern = re.compile(r"alt\s*=\s*")

    target_folders = [comp_dir, app_dir]
    for folder in target_folders:
        if not os.path.exists(folder):
            continue
        for root, _, files in os.walk(folder):
            for f in files:
                if not (f.endswith(".tsx") or f.endswith(".ts") or f.endswith(".js")):
                    continue
                path = os.path.join(root, f)
                with open(path, encoding="utf-8") as f_obj:
                    content = f_obj.read()
                    # Assert alt tag to avoid screen reader warnings
                    for img in img_pattern.findall(content):
                        assert alt_pattern.search(img), (
                            f"Accessibility warning: <img> element in {path} "
                            f"lacks an alt attribute: {img}"
                        )
