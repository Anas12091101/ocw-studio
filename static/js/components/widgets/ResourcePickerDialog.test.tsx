import React from "react"
import { act } from "react-dom/test-utils"
import { TabPane } from "reactstrap"
import { ReactWrapper } from "enzyme"

import ResourcePickerDialog from "./ResourcePickerDialog"
import IntegrationTestHelper, {
  TestRenderer
} from "../../util/integration_test_helper"
import { useDebouncedState } from "../../hooks/state"
import { useState } from "react"
import { makeWebsiteContentDetail } from "../../util/factories/websites"
import { WebsiteContent } from "../../types/websites"
import {
  RESOURCE_EMBED,
  RESOURCE_LINK
} from "../../lib/ckeditor/plugins/constants"
import {
  RESOURCE_TYPE_IMAGE,
  RESOURCE_TYPE_DOCUMENT,
  RESOURCE_TYPE_VIDEO,
  CONTENT_TYPE_PAGE
} from "../../constants"

jest.mock("../../hooks/state")

function ResourcePickerListing() {
  return <div>mock</div>
}

// mock this, otherwise it makes requests and whatnot
jest.mock("./ResourcePickerListing", () => ({
  __esModule: true,
  default:    ResourcePickerListing
}))

const focusResource = (wrapper: ReactWrapper, resource: WebsiteContent) => {
  act(() => {
    // @ts-ignore
    wrapper.find("ResourcePickerListing").prop("focusResource")(resource)
  })
  wrapper.update()
}

describe("ResourcePickerDialog", () => {
  let helper: IntegrationTestHelper,
    render: TestRenderer,
    insertEmbedStub: sinon.SinonStub,
    closeDialogStub: sinon.SinonStub,
    setStub: sinon.SinonStub,
    resource: WebsiteContent

  beforeEach(() => {
    helper = new IntegrationTestHelper()

    insertEmbedStub = helper.sandbox.stub()
    closeDialogStub = helper.sandbox.stub()
    resource = makeWebsiteContentDetail()

    setStub = helper.sandbox.stub()
    // @ts-ignore
    useDebouncedState.mockReturnValue(["", setStub])

    render = helper.configureRenderer(ResourcePickerDialog, {
      mode:        RESOURCE_EMBED,
      isOpen:      true,
      closeDialog: closeDialogStub,
      insertEmbed: insertEmbedStub
    })
  })

  afterEach(() => {
    helper.cleanup()
  })

  it("should render 3 tabs when embedding", async () => {
    const { wrapper } = await render({ mode: RESOURCE_EMBED })
    expect(wrapper.find(TabPane).map(pane => pane.prop("tabId"))).toEqual([
      RESOURCE_TYPE_DOCUMENT,
      RESOURCE_TYPE_VIDEO,
      RESOURCE_TYPE_IMAGE
    ])
  })

  it("should render 4 tabs when linking", async () => {
    const { wrapper } = await render({ mode: RESOURCE_LINK })
    expect(wrapper.find(TabPane).map(pane => pane.prop("tabId"))).toEqual([
      RESOURCE_TYPE_DOCUMENT,
      RESOURCE_TYPE_VIDEO,
      RESOURCE_TYPE_IMAGE,
      CONTENT_TYPE_PAGE
    ])
  })

  it("should pass some basic props down to the dialog", async () => {
    const { wrapper } = await render()
    const dialog = wrapper.find("Dialog")
    expect(dialog.prop("open")).toBeTruthy()
    expect(dialog.prop("wrapClassName")).toBe("resource-picker-dialog")
  })

  it("should allow focusing and linking a resource, then close the dialog", async () => {
    const { wrapper } = await render({
      mode: RESOURCE_LINK
    })
    // callback should be 'undefined' before resource is focused
    expect(wrapper.find("Dialog").prop("onAccept")).toBeUndefined()
    focusResource(wrapper, resource)

    expect(wrapper.find("Dialog").prop("acceptText")).toBe("Add link")

    act(() => {
      // @ts-ignore
      wrapper.find("Dialog").prop("onAccept")()
    })

    wrapper.update()

    expect(insertEmbedStub.args[0]).toStrictEqual([
      resource.text_id,
      resource.title,
      RESOURCE_LINK
    ])
    expect(closeDialogStub.callCount).toBe(1)
  })

  it("should focusing and embedding a resource", async () => {
    const { wrapper } = await render({
      mode: RESOURCE_EMBED
    })
    // callback should be 'undefined' before resource is focused
    expect(wrapper.find("Dialog").prop("onAccept")).toBeUndefined()
    focusResource(wrapper, resource)

    expect(wrapper.find("Dialog").prop("acceptText")).toBe("Embed resource")

    act(() => {
      // @ts-ignore
      wrapper.find("Dialog").prop("onAccept")()
    })

    wrapper.update()

    expect(insertEmbedStub.args[0]).toStrictEqual([
      resource.text_id,
      resource.title,
      RESOURCE_EMBED
    ])
  })

  it("should pass basic props to ResourcePickerListing", async () => {
    const { wrapper } = await render()
    expect(wrapper.find("ResourcePickerListing").prop("contentType")).toEqual(
      "resource"
    )
    focusResource(wrapper, resource)
    expect(wrapper.find("ResourcePickerListing").prop("focusedResource")).toBe(
      resource
    )
  })

  it("should pass correct resourcetype and contentType to active tab", async () => {
    const { wrapper } = await render({ mode: RESOURCE_LINK })

    const cases = [
      { resourcetype: RESOURCE_TYPE_DOCUMENT, contentType: "resource" },
      { resourcetype: RESOURCE_TYPE_VIDEO, contentType: "resource" },
      { resourcetype: RESOURCE_TYPE_IMAGE, contentType: "resource" },
      { resourcetype: null, contentType: "page" }
    ]
    cases.forEach(({ resourcetype, contentType }, idx) => {
      act(() => {
        wrapper
          .find("NavLink")
          .at(idx)
          .simulate("click")
      })
      wrapper.update()
      expect(
        wrapper.find("ResourcePickerListing").prop("resourcetype")
      ).toEqual(resourcetype)

      expect(wrapper.find("ResourcePickerListing").prop("contentType")).toBe(
        contentType
      )
    })
  })

  it("should pass filter string to picker, when filter is set", async () => {
    const setStub = helper.sandbox.stub()
    // @ts-ignore
    useDebouncedState.mockImplementation((initial, _ms) => {
      // this is just to un-debounce to make testing easier
      const [state, setState] = useState(initial)

      return [
        state,
        (update: any) => {
          setStub(update)
          setState(update)
        }
      ]
    })

    const { wrapper } = await render()

    act(() => {
      wrapper.find("input.filter-input").prop("onChange")!({
        // @ts-ignore
        currentTarget: { value: "new filter" }
      })
    })
    wrapper.update()

    expect(wrapper.find("ResourcePickerListing").prop("filter")).toEqual(
      "new filter"
    )
  })
})
