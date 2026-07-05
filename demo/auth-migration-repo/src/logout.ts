export type LogoutAction = {
  clearCookie: boolean
  revokeRefreshSession: boolean
  clearLocalStorage: boolean
}

export function buildLogoutAction(): LogoutAction {
  return {
    clearCookie: false,
    revokeRefreshSession: false,
    clearLocalStorage: true,
  }
}

