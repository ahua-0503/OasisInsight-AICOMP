"""Render full-width evidence images across Streamlit image API versions."""
from inspect import signature
import streamlit as st


def evidence_image(path):
    parameters = signature(st.image).parameters
    if 'width' in parameters and isinstance(parameters['width'].default, str):
        return st.image(str(path), width='stretch')
    if 'use_container_width' in parameters:
        return st.image(str(path), use_container_width=True)
    return st.image(str(path), use_column_width=True)
