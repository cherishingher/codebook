interface IAppOption {
  globalData: {
    apiBaseUrl: string
    token: string
    currentRole: null | {
      role: string
      campusId?: number
      studentId?: number
    }
  }
}

