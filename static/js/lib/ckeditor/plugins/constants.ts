export const ADD_RESOURCE_LINK = "addResourceLink"

export const ADD_RESOURCE_EMBED = "addResourceEmbed"

export const CKEDITOR_RESOURCE_UTILS = "CKEDITOR_RESOURCE_UTILS"

export const RESOURCE_EMBED = "resourceEmbed"

export const RESOURCE_LINK = "resourceLink"

export const RESOURCE_EMBED_COMMAND = "insertResourceEmbed"

import { RESOURCE_LINK_COMMAND } from "@mitodl/ckeditor5-resource-link/src/constants"
import TurndownService from "turndown"

/**
 * Union type capturing the possible typs of resource nodes we
 * support in CKEditor
 *
 * CKEResourceNodeType
 */
export type CKEResourceNodeType = typeof RESOURCE_LINK | typeof RESOURCE_EMBED

/**
 * Map resource node type to the corresponding embed command
 */
export const ResourceCommandMap: Record<CKEResourceNodeType, string> = {
  [RESOURCE_LINK]:  RESOURCE_LINK_COMMAND,
  [RESOURCE_EMBED]: RESOURCE_EMBED_COMMAND
}

/**
 * A 'resource renderer'
 *
 * A function of this type is passed down from the React component
 * that wraps CKEditor to the CKEditor config. It can then be called
 * in the `editingDowncast` handler function on the plugins for
 * resource links and embeds.
 */
export interface RenderResourceFunc {
  (uuid: string, el: HTMLElement): void
}

export type ResourceDialogMode = typeof RESOURCE_LINK | typeof RESOURCE_EMBED

export const TABLE_ELS: TurndownService.TagName[] = [
  "table",
  "tbody",
  "th",
  "td",
  "tr",
  "thead",
  "tfoot"
]
