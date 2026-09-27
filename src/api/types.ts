/** 公共库（社区池）里的一条密钥（对应后端 otherkey 表，上游密钥已打码） */
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

/** 私有库里的一条密钥（对应后端 privatekey 表，上游密钥已打码；只有本人能看到） */
export interface PrivateKeyItem {
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
}

/** 一条个人密钥（对应后端 key 表）；canuse 为空表示可使用本人私有库全部 key */
export interface PersonalKeyItem {
  key: string
  /** 允许调度的私有 key id 列表 */
  canuse: string[]
  /** 是否未限定范围（等价于 canuse 为空） */
  all: boolean
}
