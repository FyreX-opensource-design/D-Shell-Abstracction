#!/usr/bin/env bash

# Debug mode - set to 1 to enable debug output
DEBUG="${DEBUG:-0}"

# Check if a desktop file should be shown (not hidden or NoDisplay)
should_show_desktop_file() {
    local desktop_file="$1"
    if [ ! -f "$desktop_file" ]; then
        return 1
    fi
    
    # Check for NoDisplay=true
    if grep -q "^NoDisplay=true" "$desktop_file" 2>/dev/null; then
        return 1
    fi
    
    # Check for Hidden=true
    if grep -q "^Hidden=true" "$desktop_file" 2>/dev/null; then
        return 1
    fi
    
    return 0
}

# Get application name from desktop file
get_app_name() {
    local desktop_file="$1"
    if [ ! -f "$desktop_file" ]; then
        return
    fi
    
    # Try to get non-localized Name first
    name=$(grep "^Name=" "$desktop_file" 2>/dev/null | grep -v "\[" | head -n1 | sed 's/Name=//')
    
    # If no non-localized name, try to get any Name line
    if [ -z "$name" ]; then
        name=$(grep "^Name=" "$desktop_file" 2>/dev/null | head -n1 | sed 's/Name\[.*\]=//' | sed 's/Name=//')
    fi
    
    echo "$name"
}

# Check if a category is a valid XDG spec category or vendor extension
# XDG spec allows: standard categories (AudioVideo, Development, etc.) and X-* vendor extensions
is_valid_xdg_category() {
    local category="$1"
    # Must not be empty
    if [ -z "$category" ] || [ -z "${category// }" ]; then
        return 1
    fi
    
    # Allow X-* vendor extensions (like X-WayDroid-App)
    if [[ "$category" =~ ^X- ]]; then
        return 0
    fi
    
    # Standard XDG categories according to the Desktop Entry Specification
    case "$category" in
        AudioVideo|Development|Education|Game|Graphics|Network|Office|Science|Settings|System|Utility)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Get all unique categories from XDG desktop files with apps count
get_categories_with_apps() {
    local desktop_dirs="${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
    # Declare associative array at global scope
    unset category_app_count 2>/dev/null
    declare -gA category_app_count
    
    [ "$DEBUG" = "1" ] && echo "DEBUG: Starting category extraction" >&2
    [ "$DEBUG" = "1" ] && echo "DEBUG: Desktop dirs: $desktop_dirs" >&2
    
    # Process desktop files in a directory
    process_desktop_files() {
        local dir="$1"
        [ "$DEBUG" = "1" ] && echo "DEBUG: Processing directory: $dir" >&2
        if [ -d "$dir/applications" ]; then
            local file_count=0
            local processed_count=0
            while IFS= read -r desktop_file; do
                ((file_count++))
                [ "$DEBUG" = "1" ] && echo "DEBUG: Checking file: $desktop_file" >&2
                if should_show_desktop_file "$desktop_file"; then
                    app_name=$(get_app_name "$desktop_file")
                    [ "$DEBUG" = "1" ] && echo "DEBUG:   App name: '$app_name'" >&2
                    # Skip if no app name
                    if [ -z "$app_name" ]; then
                        [ "$DEBUG" = "1" ] && echo "DEBUG:   Skipping (no app name)" >&2
                        continue
                    fi
                    
                    categories_line=$(grep "^Categories=" "$desktop_file" 2>/dev/null | head -n1)
                    [ "$DEBUG" = "1" ] && echo "DEBUG:   Categories line: '$categories_line'" >&2
                    if [ -n "$categories_line" ]; then
                        # Extract categories (format: Categories=Category1;Category2;...)
                        # Filter out empty strings and trim whitespace
                        cats=$(echo "$categories_line" | sed 's/Categories=//' | tr ';' '\n' | grep -v "^$" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | grep -v "^$")
                        [ "$DEBUG" = "1" ] && echo "DEBUG:   Extracted categories: $(echo "$cats" | tr '\n' ',')" >&2
                        
                        # Count apps for each valid XDG category
                        while IFS= read -r cat; do
                            [ "$DEBUG" = "1" ] && echo "DEBUG:     Checking category: '$cat'" >&2
                            if is_valid_xdg_category "$cat"; then
                                # Increment count for this category
                                category_app_count["$cat"]=$((${category_app_count["$cat"]:-0} + 1))
                                [ "$DEBUG" = "1" ] && echo "DEBUG:     Valid! Count for '$cat': ${category_app_count["$cat"]}" >&2
                                ((processed_count++))
                            else
                                [ "$DEBUG" = "1" ] && echo "DEBUG:     Invalid XDG category (filtered out)" >&2
                            fi
                        done < <(echo "$cats")
                    else
                        [ "$DEBUG" = "1" ] && echo "DEBUG:   No categories line found" >&2
                    fi
                else
                    [ "$DEBUG" = "1" ] && echo "DEBUG:   Skipping (should_show_desktop_file returned false)" >&2
                fi
            done < <(find "$dir/applications" -name "*.desktop" 2>/dev/null)
            [ "$DEBUG" = "1" ] && echo "DEBUG: Processed $processed_count apps from $file_count files in $dir" >&2
        else
            [ "$DEBUG" = "1" ] && echo "DEBUG: Directory does not exist: $dir/applications" >&2
        fi
    }
    
    IFS=':' read -ra DIRS <<< "$desktop_dirs"
    for dir in "${DIRS[@]}"; do
        process_desktop_files "$dir"
    done
    
    # Also check user's local applications (this is already the applications directory, not a parent)
    if [ -d "$HOME/.local/share/applications" ]; then
        [ "$DEBUG" = "1" ] && echo "DEBUG: Processing user local applications: $HOME/.local/share/applications" >&2
        local file_count=0
        local processed_count=0
        while IFS= read -r desktop_file; do
            ((file_count++))
            [ "$DEBUG" = "1" ] && echo "DEBUG: Checking file: $desktop_file" >&2
            if should_show_desktop_file "$desktop_file"; then
                app_name=$(get_app_name "$desktop_file")
                [ "$DEBUG" = "1" ] && echo "DEBUG:   App name: '$app_name'" >&2
                if [ -z "$app_name" ]; then
                    [ "$DEBUG" = "1" ] && echo "DEBUG:   Skipping (no app name)" >&2
                    continue
                fi
                
                categories_line=$(grep "^Categories=" "$desktop_file" 2>/dev/null | head -n1)
                [ "$DEBUG" = "1" ] && echo "DEBUG:   Categories line: '$categories_line'" >&2
                if [ -n "$categories_line" ]; then
                    cats=$(echo "$categories_line" | sed 's/Categories=//' | tr ';' '\n' | grep -v "^$" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | grep -v "^$")
                    [ "$DEBUG" = "1" ] && echo "DEBUG:   Extracted categories: $(echo "$cats" | tr '\n' ',')" >&2
                    
                    while IFS= read -r cat; do
                        [ "$DEBUG" = "1" ] && echo "DEBUG:     Checking category: '$cat'" >&2
                        if is_valid_xdg_category "$cat"; then
                            category_app_count["$cat"]=$((${category_app_count["$cat"]:-0} + 1))
                            [ "$DEBUG" = "1" ] && echo "DEBUG:     Valid! Count for '$cat': ${category_app_count["$cat"]}" >&2
                            ((processed_count++))
                        else
                            [ "$DEBUG" = "1" ] && echo "DEBUG:     Invalid XDG category (filtered out)" >&2
                        fi
                    done < <(echo "$cats")
                else
                    [ "$DEBUG" = "1" ] && echo "DEBUG:   No categories line found" >&2
                fi
            else
                [ "$DEBUG" = "1" ] && echo "DEBUG:   Skipping (should_show_desktop_file returned false)" >&2
            fi
        done < <(find "$HOME/.local/share/applications" -name "*.desktop" 2>/dev/null)
        [ "$DEBUG" = "1" ] && echo "DEBUG: Processed $processed_count apps from $file_count files in $HOME/.local/share/applications" >&2
    else
        [ "$DEBUG" = "1" ] && echo "DEBUG: User local applications dir does not exist" >&2
    fi
    
    [ "$DEBUG" = "1" ] && echo "DEBUG: Total categories found: ${#category_app_count[@]}" >&2
    [ "$DEBUG" = "1" ] && echo "DEBUG: Category keys: ${!category_app_count[*]}" >&2
    
    # Output categories that have at least one app, sorted
    for category in "${!category_app_count[@]}"; do
        local count="${category_app_count[$category]:-0}"
        [ "$DEBUG" = "1" ] && echo "DEBUG: Category '$category' has count: $count" >&2
        if [ "$count" -gt 0 ]; then
            echo "$category"
        fi
    done | sort
}

# Get all unique categories from XDG desktop files (backward compatibility)
get_categories() {
    get_categories_with_apps
}

# Get applications for a specific category
get_apps_in_category() {
    local category="$1"
    local desktop_dirs="${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
    local apps=""
    
    [ "$DEBUG" = "1" ] && echo "DEBUG: get_apps_in_category called for category: '$category'" >&2
    [ "$DEBUG" = "1" ] && echo "DEBUG: Desktop dirs: $desktop_dirs" >&2
    
    IFS=':' read -ra DIRS <<< "$desktop_dirs"
    for dir in "${DIRS[@]}"; do
        [ "$DEBUG" = "1" ] && echo "DEBUG: Checking directory: $dir/applications" >&2
        if [ -d "$dir/applications" ]; then
            while IFS= read -r desktop_file; do
                [ "$DEBUG" = "1" ] && echo "DEBUG:   Checking file: $desktop_file" >&2
                if should_show_desktop_file "$desktop_file"; then
                    # Check if desktop file has the category
                    categories_line=$(grep "^Categories=" "$desktop_file" 2>/dev/null | head -n1)
                    [ "$DEBUG" = "1" ] && echo "DEBUG:     Categories line: '$categories_line'" >&2
                    if [ -n "$categories_line" ]; then
                        # Extract just the categories value (remove "Categories=" prefix)
                        categories_value=$(echo "$categories_line" | sed 's/^Categories=//')
                        # Escape special regex characters in category name
                        category_escaped=$(printf '%s\n' "$category" | sed 's/[[\.*^$()+?{|]/\\&/g')
                        [ "$DEBUG" = "1" ] && echo "DEBUG:     Matching category '$category' (escaped: '$category_escaped') against categories value '$categories_value'" >&2
                        if echo "$categories_value" | grep -qE "(^|;)$category_escaped(;|$)"; then
                            app_name=$(get_app_name "$desktop_file")
                            [ "$DEBUG" = "1" ] && echo "DEBUG:     Category match! App name: '$app_name'" >&2
                            if [ -n "$app_name" ]; then
                                [ "$DEBUG" = "1" ] && echo "DEBUG: Found app: '$app_name' in $desktop_file" >&2
                                apps+="$app_name|$desktop_file"$'\n'
                            else
                                [ "$DEBUG" = "1" ] && echo "DEBUG:     No app name found" >&2
                            fi
                        else
                            [ "$DEBUG" = "1" ] && echo "DEBUG:     Category does not match" >&2
                        fi
                    else
                        [ "$DEBUG" = "1" ] && echo "DEBUG:     No categories line found" >&2
                    fi
                else
                    [ "$DEBUG" = "1" ] && echo "DEBUG:     File should not be shown" >&2
                fi
            done < <(find "$dir/applications" -name "*.desktop" 2>/dev/null)
        fi
    done
    
    # Also check user's local applications
    [ "$DEBUG" = "1" ] && echo "DEBUG: Checking user local applications: $HOME/.local/share/applications" >&2
    if [ -d "$HOME/.local/share/applications" ]; then
        while IFS= read -r desktop_file; do
            [ "$DEBUG" = "1" ] && echo "DEBUG:   Checking file: $desktop_file" >&2
            if should_show_desktop_file "$desktop_file"; then
                categories_line=$(grep "^Categories=" "$desktop_file" 2>/dev/null | head -n1)
                [ "$DEBUG" = "1" ] && echo "DEBUG:     Categories line: '$categories_line'" >&2
                if [ -n "$categories_line" ]; then
                    # Extract just the categories value (remove "Categories=" prefix)
                    categories_value=$(echo "$categories_line" | sed 's/^Categories=//')
                    # Escape special regex characters in category name
                    category_escaped=$(printf '%s\n' "$category" | sed 's/[[\.*^$()+?{|]/\\&/g')
                    [ "$DEBUG" = "1" ] && echo "DEBUG:     Matching category '$category' (escaped: '$category_escaped') against categories value '$categories_value'" >&2
                    if echo "$categories_value" | grep -qE "(^|;)$category_escaped(;|$)"; then
                        app_name=$(get_app_name "$desktop_file")
                        [ "$DEBUG" = "1" ] && echo "DEBUG:     Category match! App name: '$app_name'" >&2
                        if [ -n "$app_name" ]; then
                            [ "$DEBUG" = "1" ] && echo "DEBUG: Found app: '$app_name' in $desktop_file" >&2
                            apps+="$app_name|$desktop_file"$'\n'
                        else
                            [ "$DEBUG" = "1" ] && echo "DEBUG:     No app name found" >&2
                        fi
                    else
                        [ "$DEBUG" = "1" ] && echo "DEBUG:     Category does not match" >&2
                    fi
                else
                    [ "$DEBUG" = "1" ] && echo "DEBUG:     No categories line found" >&2
                fi
            else
                [ "$DEBUG" = "1" ] && echo "DEBUG:     File should not be shown" >&2
            fi
        done < <(find "$HOME/.local/share/applications" -name "*.desktop" 2>/dev/null)
    fi
    
    [ "$DEBUG" = "1" ] && echo "DEBUG: Total apps found: $(echo "$apps" | grep -v "^$" | wc -l)" >&2
    
    # Sort by name and remove duplicates based on desktop file path (keep first occurrence)
    echo "$apps" | awk -F'|' '!seen[$1]++' | sort -t'|' -k1,1
}

# Launch an application from its desktop file
launch_app() {
    local desktop_file="$1"
    if [ ! -f "$desktop_file" ]; then
        return 1
    fi
    
    # Try gtk-launch first (works with desktop file basename)
    if command -v gtk-launch &> /dev/null; then
        gtk-launch "$(basename "$desktop_file")" 2>/dev/null && return 0
    fi
    
    # Try desktop-file-launch
    if command -v desktop-file-launch &> /dev/null; then
        desktop-file-launch "$desktop_file" 2>/dev/null && return 0
    fi
    
    # Fallback: extract Exec line and run it
    exec_line=$(grep "^Exec=" "$desktop_file" 2>/dev/null | head -n1 | sed 's/Exec=//')
    if [ -n "$exec_line" ]; then
        # Remove desktop file specifiers (%f, %F, %u, %U, etc.)
        exec_line=$(echo "$exec_line" | sed 's/%[fFuUdDnNickvm]//g')
        # Execute in background
        eval "$exec_line" &
    fi
}

# Main menu - show categories (already filtered to only show categories with apps)
[ "$DEBUG" = "1" ] && echo "DEBUG: Getting categories..." >&2
CATEGORIES=$(get_categories_with_apps)
[ "$DEBUG" = "1" ] && echo "DEBUG: Categories found:" >&2
[ "$DEBUG" = "1" ] && echo "$CATEGORIES" | while read -r cat; do echo "DEBUG:   - $cat" >&2; done
[ "$DEBUG" = "1" ] && echo "DEBUG: Showing wofi menu..." >&2
SELECTED_CATEGORY=$(echo -e "All Applications\n$CATEGORIES" | grep -v "^$" | exec -a "wofi-app-menu" wofi -d --prompt "Categories: " --style "$WOFI_THEME/wofi/style.css")
[ "$DEBUG" = "1" ] && echo "DEBUG: Selected category: '$SELECTED_CATEGORY'" >&2

# If a category was selected, show apps in that category
if [ -n "$SELECTED_CATEGORY" ]; then
    # Handle "All Applications" - show drun menu
    if [ "$SELECTED_CATEGORY" = "All Applications" ]; then
        [ "$DEBUG" = "1" ] && echo "DEBUG: Showing drun menu..." >&2
        exec -a "wofi-app-menu" wofi --conf "$WOFI_THEME/wofi/config" --style "$WOFI_THEME/wofi/style.css" --show drun
        exit 0
    fi
    
    # Show apps in the selected category with a Back option
    [ "$DEBUG" = "1" ] && echo "DEBUG: Getting apps for category: '$SELECTED_CATEGORY'" >&2
    APPS=$(get_apps_in_category "$SELECTED_CATEGORY")
    
    [ "$DEBUG" = "1" ] && echo "DEBUG: Apps found:" >&2
    [ "$DEBUG" = "1" ] && echo "$APPS" | while IFS='|' read -r name file; do [ -n "$name" ] && echo "DEBUG:   - $name ($file)" >&2; done
    
    if [ -z "$APPS" ]; then
        [ "$DEBUG" = "1" ] && echo "DEBUG: No apps found, exiting" >&2
        exit 0
    fi
    
    # Extract just the app names for display, add Back option
    APP_NAMES=$(echo "$APPS" | cut -d'|' -f1)
    [ "$DEBUG" = "1" ] && echo "DEBUG: Showing wofi menu for apps..." >&2
    SELECTED_APP=$(echo -e "← Back\n$APP_NAMES" | exec -a "wofi-app-menu" wofi -d --prompt "$SELECTED_CATEGORY: " --style "$WOFI_THEME/wofi/style.css")
    [ "$DEBUG" = "1" ] && echo "DEBUG: Selected app: '$SELECTED_APP'" >&2
    
    # If Back was selected, restart the script to show categories again
    if [ "$SELECTED_APP" = "← Back" ]; then
        [ "$DEBUG" = "1" ] && echo "DEBUG: Back selected, restarting..." >&2
        exec "$0" "$@"
        exit 0
    fi
    
    # If an app was selected, find its desktop file and launch it
    if [ -n "$SELECTED_APP" ]; then
        SELECTED_DESKTOP=$(echo "$APPS" | grep "^$SELECTED_APP|" | head -n1 | cut -d'|' -f2)
        [ "$DEBUG" = "1" ] && echo "DEBUG: Desktop file to launch: '$SELECTED_DESKTOP'" >&2
        if [ -n "$SELECTED_DESKTOP" ]; then
            launch_app "$SELECTED_DESKTOP"
            [ "$DEBUG" = "1" ] && echo "DEBUG: Launch command executed" >&2
        else
            [ "$DEBUG" = "1" ] && echo "DEBUG: No desktop file found for selected app" >&2
        fi
    fi
fi

