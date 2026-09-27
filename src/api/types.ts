/** 社区池里的一条密钥（对应后端 otherkey 表，上游密钥已打码） */
export interface CommunityKeyItem {
  id: string
  key: string
  url: string
  model: string
  name: string | null
  protocol: string
  priority: number
  maxuse: number | null
  used: number
  remaining: number | null
  enabled: boolean
  text: string | null
  createdAt: number
  /** 是否是当前登录用户上传的（决定是否显示删除按钮） */
  mine: boolean
}
