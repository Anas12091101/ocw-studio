import moment from "moment"
import sinon, { SinonStub } from "sinon"
import { act } from "react-dom/test-utils"

import { siteApiActionUrl, siteApiDetailUrl } from "../lib/urls"
import IntegrationTestHelper, {
  TestRenderer
} from "../util/integration_test_helper"
import { makeWebsiteDetail } from "../util/factories/websites"
import PublishDrawer from "./PublishDrawer"
import { Website } from "../types/websites"

describe("PublishDrawer", () => {
  let helper: IntegrationTestHelper,
    website: Website,
    render: TestRenderer,
    toggleVisibilityStub: SinonStub,
    refreshWebsiteStub: SinonStub

  beforeEach(() => {
    helper = new IntegrationTestHelper()
    toggleVisibilityStub = helper.sandbox.stub()
    website = {
      ...makeWebsiteDetail(),
      has_unpublished_draft: true,
      has_unpublished_live:  true,
      is_admin:              true
    }
    refreshWebsiteStub = helper.handleRequestStub
      .withArgs(siteApiDetailUrl.param({ name: website.name }).toString())
      .returns({ body: website, status: 200 })
    render = helper.configureRenderer(
      PublishDrawer,
      {
        website,
        visibility:       true,
        toggleVisibility: toggleVisibilityStub
      },
      {
        entities: {},
        queries:  {}
      }
    )

    helper.mockGetRequest(
      siteApiDetailUrl.param({ name: website.name }).toString(),
      website
    )
  })

  afterEach(() => {
    helper.cleanup()
  })

  //
  ;[
    [
      "staging",
      "preview",
      "has_unpublished_draft",
      "Staging",
      "draft_url",
      "draft_publish_date",
      0
    ],
    [
      "production",
      "publish",
      "has_unpublished_live",
      "Production",
      "live_url",
      "publish_date",
      1
    ]
  ].forEach(
    ([
      action,
      api,
      unpublishedField,
      label,
      urlField,
      publishDateField,
      idx
    ]) => {
      describe(action, () => {
        [true, false].forEach(visible => {
          it(`renders inside a Modal when visibility=${visible}`, async () => {
            const { wrapper } = await render({ visibility: visible })
            expect(wrapper.find("Modal").prop("isOpen")).toEqual(visible)
            expect(wrapper.find("Modal").prop("toggle")).toEqual(
              toggleVisibilityStub
            )
            if (visible) {
              expect(wrapper.find("ModalHeader").prop("toggle")).toEqual(
                toggleVisibilityStub
              )
            }
          })
        })

        it("renders the date and url", async () => {
          const { wrapper } = await render()
          await act(async () => {
            // @ts-ignore
            wrapper
              .find("input[type='radio']")
              // @ts-ignore
              .at(idx)
              // @ts-ignore
              .prop("onChange")()
          })
          await wrapper.update()
          expect(wrapper.find(".publish-option-description").text()).toContain(
            `Last updated: ${moment(website[publishDateField]).format(
              "dddd, MMMM D h:mma ZZ"
            )}`
          )
          expect(
            wrapper.find(".publish-option-description a").prop("href")
          ).toBe(website[urlField])
          expect(wrapper.find(".publish-option-description a").text()).toBe(
            website[urlField]
          )
        })

        it("renders a message if there is no date", async () => {
          website[publishDateField] = null
          const { wrapper } = await render()
          await act(async () => {
            // @ts-ignore
            wrapper
              .find("input[type='radio']")
              // @ts-ignore
              .at(idx)
              // @ts-ignore
              .prop("onChange")()
          })
          await wrapper.update()
          expect(wrapper.find(".publish-option-description").text()).toContain(
            "Last updated: never published"
          )
        })

        it("has an option with the right label", async () => {
          const { wrapper } = await render()
          await act(async () => {
            // @ts-ignore
            wrapper
              .find("input[type='radio']")
              // @ts-ignore
              .at(idx)
              // @ts-ignore
              .prop("onChange")()
          })
          await wrapper.update()
          // @ts-ignore
          expect(
            wrapper
              .find(".publish-option label")
              // @ts-ignore
              .at(idx)
              .text()
          ).toBe(label)
        })

        it("disables the button if there is no unpublished content", async () => {
          website[unpublishedField] = false
          const { wrapper } = await render()
          await act(async () => {
            // @ts-ignore
            wrapper.find(`#publish-${action}`).prop("onChange")()
          })
          await wrapper.update()
          expect(wrapper.find(".btn-publish").prop("disabled")).toBe(true)
        })

        it("render only the preview button if user is not an admin", async () => {
          website["is_admin"] = false
          const { wrapper } = await render()
          expect(wrapper.find(`#publish-${action}`).exists()).toBe(
            action === "staging" ? true : false
          )
        })

        it("renders a message about unpublished content", async () => {
          website[unpublishedField] = true
          const { wrapper } = await render()
          await act(async () => {
            // @ts-ignore
            wrapper.find(`#publish-${action}`).prop("onChange")()
          })
          await wrapper.update()
          expect(wrapper.find(".publish-option-description").text()).toContain(
            "You have unpublished changes."
          )
        })

        it("renders an error message if the publish didn't work", async () => {
          const actionStub = helper.handleRequestStub
            .withArgs(
              siteApiActionUrl
                .param({
                  name:   website.name,
                  action: api
                })
                .toString()
            )
            .returns({
              status: 500
            })
          const { wrapper } = await render()
          await act(async () => {
            // @ts-ignore
            wrapper.find(`#publish-${action}`).prop("onChange")()
          })
          await wrapper.update()
          await act(async () => {
            // @ts-ignore
            wrapper.find(".btn-publish").prop("onClick")()
          })
          await wrapper.update()
          expect(wrapper.find(".publish-option-description").text()).toContain(
            "We apologize, there was an error publishing the site. Please try again in a few minutes."
          )
          sinon.assert.calledOnceWithExactly(
            actionStub,
            `/api/websites/${website.name}/${api}/`,
            "POST",
            {
              body:        {},
              headers:     { "X-CSRFTOKEN": "" },
              credentials: undefined
            }
          )
          sinon.assert.notCalled(refreshWebsiteStub)
          sinon.assert.notCalled(toggleVisibilityStub)
        })

        it("publish button sends the expected request", async () => {
          const actionStub = helper.handleRequestStub
            .withArgs(
              siteApiActionUrl
                .param({
                  name:   website.name,
                  action: api
                })
                .toString()
            )
            .returns({
              status: 200
            })
          const { wrapper } = await render()
          await act(async () => {
            // @ts-ignore
            wrapper.find(`#publish-${action}`).prop("onChange")()
          })
          await wrapper.update()
          expect(wrapper.find(".btn-publish").prop("disabled")).toBeFalsy()
          await act(async () => {
            // @ts-ignore
            wrapper.find(".btn-publish").prop("onClick")()
          })
          sinon.assert.calledOnceWithExactly(
            actionStub,
            `/api/websites/${website.name}/${api}/`,
            "POST",
            {
              body:        {},
              headers:     { "X-CSRFTOKEN": "" },
              credentials: undefined
            }
          )
          sinon.assert.calledOnceWithExactly(
            refreshWebsiteStub,
            `/api/websites/${website.name}/`,
            "GET",
            {
              body:        undefined,
              headers:     undefined,
              credentials: undefined
            }
          )
          sinon.assert.calledOnceWithExactly(toggleVisibilityStub)
        })
      })
    }
  )
})