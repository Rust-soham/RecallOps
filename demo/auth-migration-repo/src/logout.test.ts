import { describe, expect, it } from "vitest"
import { buildLogoutAction } from "./logout"

describe("logout security contract", () => {
  it("clears the cookie and revokes the refresh session", () => {
    expect(buildLogoutAction()).toEqual({
      clearCookie: true,
      revokeRefreshSession: true,
      clearLocalStorage: false,
    })
  })
})

