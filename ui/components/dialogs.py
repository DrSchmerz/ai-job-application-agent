"""
Dialog components for confirmations and user interactions.
"""
import streamlit as st


def confirm_delete(item_name: str, key: str = "confirm") -> bool:
    """
    Show a confirmation dialog for delete action.

    Args:
        item_name: Name of the item to delete (e.g., company name)
        key: Unique key for the confirmation checkbox

    Returns:
        True if user confirmed deletion, False otherwise
    """
    st.warning(f"⚠️ Are you sure you want to delete **{item_name}**?")
    st.caption("This action cannot be undone.")

    confirm = st.checkbox(
        "Yes, I want to permanently delete this application",
        key=f"{key}_checkbox"
    )

    if confirm:
        if st.button("🗑️ Confirm Delete", type="primary", key=f"{key}_button"):
            return True

    return False


def confirm_bulk_delete(count: int, key: str = "bulk_confirm") -> bool:
    """
    Show confirmation dialog for bulk delete.

    Args:
        count: Number of items to delete
        key: Unique key for the confirmation

    Returns:
        True if user confirmed, False otherwise
    """
    st.error(f"⚠️ You are about to delete **{count} applications**")
    st.caption("This action cannot be undone.")

    confirm = st.checkbox(
        f"Yes, I want to permanently delete {count} applications",
        key=f"{key}_checkbox"
    )

    if confirm:
        if st.button("🗑️ Confirm Bulk Delete", type="primary", key=f"{key}_button"):
            return True

    return False


def confirm_action(
    message: str,
    action_name: str,
    warning_level: str = "warning",
    key: str = "confirm"
) -> bool:
    """
    Generic confirmation dialog.

    Args:
        message: Message to show user
        action_name: Name of action (e.g., "Archive", "Reset")
        warning_level: "warning", "error", or "info"
        key: Unique key for the dialog

    Returns:
        True if confirmed, False otherwise
    """
    if warning_level == "error":
        st.error(message)
    elif warning_level == "info":
        st.info(message)
    else:
        st.warning(message)

    confirm = st.checkbox(
        f"Yes, proceed with {action_name}",
        key=f"{key}_checkbox"
    )

    if confirm:
        if st.button(f"✓ Confirm {action_name}", type="primary", key=f"{key}_button"):
            return True

    return False
