"""Context provider for the workflow visualization page."""
import frappe


def get_context(context):
    context.no_cache = 1
    context.title = "Case Workflow"
