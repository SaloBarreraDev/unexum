from kivy.utils import platform
if platform == "android":
    try:
        from jnius import PythonJavaClass, autoclass, cast, java_method
        Environment = autoclass("android.os.Environment")
    except ImportError:
        Logger.error(f"Error de importación de modulos android")
    try:
        from android import api_version  # type: ignore
    except:
        Logger.warning(f"No se pudo determinar la versión de api, usando 0")
        api_version = 0

def get_height_of_bar(bar_target=None):
    bar_target = bar_target or "status"

    if bar_target not in ("status", "navigation"):
        raise Exception("bar_target must be 'status' or 'navigation'")

    try:
        displayMetrics = autoclass("android.util.DisplayMetrics")
        mActivity.getWindowManager().getDefaultDisplay().getMetrics(displayMetrics())
        resources = mActivity.getResources()
        resourceId = resources.getIdentifier(
            f"{bar_target}_bar_height", "dimen", "android"
        )

        return float(max(resources.getDimensionPixelSize(resourceId), 0))
    except Exception:
        # Getting the size is not supported on older Androids
        return 0.0


def set_status_bar_color(color_hex):
    if platform == "android":
        try:
            # Get the Android activity
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            activity = cast("android.app.Activity", PythonActivity.mActivity)

            @run_on_ui_thread
            def setup_status_bar():
                """Setup status bar color on the main thread."""
                try:
                    # Get window and set status bar color
                    window = activity.getWindow()

                    # Get Android constants - access nested class properly
                    LayoutParams = autoclass("android.view.WindowManager$LayoutParams")

                    # Clear the translucent status bar flag and add
                    # system bar backgrounds
                    window.clearFlags(LayoutParams.FLAG_TRANSLUCENT_STATUS)
                    window.addFlags(LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS)

                    # Convert hex to Android color int
                    Color = autoclass("android.graphics.Color")
                    color_int = Color.parseColor(color_hex)

                    # Set the status bar color
                    window.setStatusBarColor(color_int)

                except Exception as e:
                    Logger.error(f"Failed to set status bar color: {e}")

            # Run on UI thread using decorator
            setup_status_bar()

        except Exception as e:
            Logger.error(f"Failed to set status bar color: {e}")


def set_status_bar_icons_dark(dark):
    if platform == "android":
        try:
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            activity = cast("android.app.Activity", PythonActivity.mActivity)

            @run_on_ui_thread
            def setup_status_bar_icons():
                """Setup status bar icons on the main thread."""
                try:
                    # Get Android View class for constants
                    View = autoclass("android.view.View")

                    window = activity.getWindow()
                    view = window.getDecorView()

                    # Get current system UI flags
                    current_flags = view.getSystemUiVisibility()

                    if dark:
                        # Add light status bar flag (dark icons)
                        new_flags = current_flags | View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR
                    else:
                        # Remove light status bar flag (light icons)
                        new_flags = (
                            current_flags & ~View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR
                        )

                    view.setSystemUiVisibility(new_flags)

                    icon_type = "dark" if dark else "light"

                except Exception as e:
                    Logger.error(f"Failed to set status bar icons: {e}")

            # Run on UI thread using decorator
            setup_status_bar_icons()

        except Exception as e:
            Logger.error(f"Failed to set status bar icons: {e}")


def set_navigation_bar_black(dark):
    """
    Set the navigation bar (bottom bar) color to black.

    This function specifically changes the bottom navigation bar color
    to black, which can be useful for creating a consistent dark theme
    or matching specific design requirements.
    """
    if platform != "android":
        return False

    try:
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        activity = cast("android.app.Activity", PythonActivity.mActivity)

        @run_on_ui_thread
        def setup_navigation_bar():
            """Set navigation bar color to black on the main thread."""
            try:
                window = activity.getWindow()

                # Get Android constants and Color class
                LayoutParams = autoclass("android.view.WindowManager$LayoutParams")
                Color = autoclass("android.graphics.Color")

                # Enable system bar backgrounds to allow color changes
                window.addFlags(LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS)

                # Set navigation bar color to black
                if dark:
                    window.setNavigationBarColor(Color.BLACK)
                else:
                    window.setNavigationBarColor(Color.WHITE)

            except Exception as e:
                Logger.error(f"Failed to set navigation bar color: {e}")

        # Run on UI thread using decorator
        setup_navigation_bar()
        return True

    except Exception as e:
        return False