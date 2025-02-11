import sys
import pytest

if __name__ == "__main__":
    # Add the src directory to Python path
    sys.path.append("/app")

    # Run pytest with the test file
    pytest.main(["-v", "src/blender/test_blender.py"])
