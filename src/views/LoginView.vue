<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '../components/AppIcon.vue'
import AuthCard from '../components/AuthCard.vue'
import { api, withDemo } from '../api/client'
import { session } from '../store/session'
import { toast } from '../store/toast'

const route = useRoute()
const router = useRouter()

const form = reactive({ email: '', password: '' })
const loading = ref(false)
const error = ref('')

const redirect = computed(() =>
  typeof route.query.redirect === 'string' && route.query.redirect ? route.query.redirect : '/console',
)

async function submit(): Promise<void> {
  error.value = ''
  if (!form.email || !form.password) {
    error.value = '请输入邮箱与密码'
    return
  }

  loading.value = true
  try {
    // 后端不可用时，withDemo 会回退到本地占位数据（不做真实鉴权）
    await withDemo(
      () => api.signIn(form.email, form.password),
      () => undefined,
    )
    session.signIn({ name: form.email.split('@')[0], email: form.email })
    toast.ok('登录成功')
    await router.push(redirect.value)
  } catch (err) {
    error.value = err instanceof Error ? err.message : '登录失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthCard
    title="登录 AIHub"
    subtitle="使用注册邮箱继续，密钥保存在你的账号下"
    foot-text="还没有账号？"
    foot-link-text="免费注册"
    foot-link-to="/register"
  >
    <form class="form" @submit.prevent="submit">
      <div class="field">
        <label class="field__label" for="login-email">邮箱</label>
        <input
          id="login-email"
          v-model.trim="form.email"
          class="input"
          type="email"
          autocomplete="email"
          placeholder="you@example.com"
        />
      </div>

      <div class="field">
        <label class="field__label" for="login-password">密码</label>
        <input
          id="login-password"
          v-model="form.password"
          class="input"
          type="password"
          autocomplete="current-password"
          placeholder="至少 8 位"
        />
      </div>

      <p v-if="error" class="alert alert--error">
        <AppIcon name="alert" :size="15" />
        {{ error }}
      </p>

      <button class="btn btn--primary btn--block" type="submit" :disabled="loading">
        {{ loading ? '登录中…' : '登录' }}
        <AppIcon v-if="!loading" name="arrow-right" :size="16" />
      </button>
    </form>

    <p class="hint">
      <AppIcon name="lock" :size="13" />
      后端使用 HttpOnly Cookie 保存登录态，前端不接触凭证。
    </p>
  </AuthCard>
</template>

<style scoped>
.form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 14px;
  font-size: 12.5px;
  color: var(--text-soft);
}
</style>
