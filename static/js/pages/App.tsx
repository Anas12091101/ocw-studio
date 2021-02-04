import React from "react"
import { Route, Switch } from "react-router"

import SitePage from "./SitePage"
import Header from "../components/Header"
import MarkdownEditorTestPage from "./MarkdownEditorTestPage"
import useTracker from "../hooks/tracker"

export default function App(): JSX.Element {
  useTracker()

  return (
    <div className="app">
      <Header />
      <Switch>
        <Route path="/sites/:name" component={SitePage} />
        <Route path="/markdown-editor">
          <MarkdownEditorTestPage />
        </Route>
      </Switch>
    </div>
  )
}
