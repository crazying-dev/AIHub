<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppIcon from '../components/AppIcon.vue'
import AuthCard from '../components/AuthCard.vue'
import { api } from '../api/client'
import { toast } from '../store/toast'

const router = useRouter()

/** 两步式注册：1. 邮箱收验证码；2. 验证码 + 用户名 + 密码 */
const step = ref<1 | 2>(1)
const sending = ref(false)
const submitting = ref(false)
const error = ref('')
const countdown = ref(0)

const form = reactive({
  email: '',
  code: '',
  name: '',
  password: '',
  confirm: '',
})

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const codeFilled = computed(() => form.code.replace(/\D/g, '').length === 6)

let timer: number | undefined

function startCountdown(): void {
  countdown.value = 60
  window.clearInterval(timer)
  timer = window.setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0) {
      window.clearInterval(timer)
    }
  }, 1000)
}

async function sendCode(): Promise<void> {
  error.value = ''
  if (!EMAIL_RE.test(form.email)) {
    error.value = '请输入合法的邮箱地址'
    return
  }

  sending.value = true
  try {
    await api.sendSignUpCode(form.email)
    step.value = 2
    startCountdown()
    toast.ok('验证码已发送，请查收邮件')
  } catch (err) {
    error.value = err instanceof Error ? err.message : '验证码发送失败'
  } finally {
    sending.value = false
  }
}

async function submit(): Promise<void> {
  error.value = ''
  if (!codeFilled.value) {
    error.value = '请输入 6 位邮箱验证码'
    return
  }
  if (form.name.trim().length < 2) {
    error.value = '用户名至少 2 个字符'
    return
  }
  if (form.password.length < 8) {
    error.value = '密码至少 8 位'
    return
  }
  if (form.password !== form.confirm) {
    error.value = '两次输入的密码不一致'
    return
  }

  submitting.value = true
  try {
    await api.signUp({ email: form.email, code: form.code, name: form.name.trim(), password: form.password })
    toast.ok('注册成功，请使用该邮箱登录')
    await router.push({ name: 'login' })
  } catch (err) {
    error.value = err instanceof Error ? err.message : '注册失败，请稍后重试'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <AuthCard
    title="创建 AIHub 账号"
    subtitle="注册后即可创建密钥并调用全部模型"
    foot-text="已经有账号了？"
    foot-link-text="去登录"
    foot-link-to="/login"
  >
    <ol class="steps">
      <li class="steps__item" :class="{ 'steps__item--active': step === 1 }">
        <span class="steps__dot">1</span> 验证邮箱
      </li>
      <li class="steps__item" :class="{ 'steps__item--active': step === 2 }">
        <span class="steps__dot">2</span> 设置账号
      </li>
    </ol>

    <form class="form" @submit.prevent="step === 1 ? sendCode() : submit()">
      <div class="field">
        <label class="field__label" for="reg-email">邮箱</label>
        <input
          id="reg-email"
          v-model.trim="form.email"
          class="input"
          type="email"
          autocomplete="email"
          placeholder="you@example.com"
          :disabled="step === 2"
        />
        <span class="field__hint">用于接收验证码，同一个邮箱只能注册一个账号。</span>
      </div>

      <template v-if="step === 2">
        <div class="field">
          <div class="field__row">
            <label class="field__label" for="reg-code">邮箱验证码</label>
            <button
              type="button"
              class="link-btn"
              :disabled="countdown > 0 || sending"
              @click="sendCode"
            >
              {{ countdown > 0 ? `${countdown}s 后重新发送` : '重新发送' }}
            </button>
          </div>
          <input
            id="reg-code"
            v-model.trim="form.code"
            class="input input--mono"
            inputmode="numeric"
            maxlength="6"
            placeholder="6 位数字"
          />
        </div>

        <div class="field">
          <label class="field__label" for="reg-name">用户名</label>
          <input
            id="reg-name"
            v-model.trim="form.name"
            class="input"
            autocomplete="nickname"
            placeholder="例如 alan"
          />
        </div>

        <div class="grid-2">
          <div class="field">
            <label class="field__label" for="reg-password">密码</label>
            <input
              id="reg-password"
              v-model="form.password"
              class="input"
              type="password"
              autocomplete="new-password"
              placeholder="至少 8 位"
            />
          </div>
          <div class="field">
            <label class="field__label" for="reg-confirm">确认密码</label>
            <input
              id="reg-confirm"
              v-model="form.confirm"
              class="input"
              type="password"
              autocomplete="new-password"
              placeholder="再输一次"
            />
          </div>
        </div>
      </template>

      <p v-if="error" class="alert alert--error">
        <AppIcon name="alert" :size="15" />
        {{ error }}
      </p>

      <button
        v-if="step === 1"
        class="btn btn--primary btn--block"
        type="submit"
        :disabled="sending"
      >
        {{ sending ? '发送中…' : '发送验证码' }}
        <AppIcon v-if="!sending" name="arrow-right" :size="16" />
      </button>

      <div v-else class="actions">
        <button class="btn" type="button" @click="step = 1">返回上一步</button>
        <button class="btn btn--primary" type="submit" :disabled="submitting">
          {{ submitting ? '提交中…' : '完成注册' }}
        </button>
      </div>
    </form>
  </AuthCard>
</template>

<style scoped>
.steps {
  display: flex;
  gap: 10px;
  margin: 0 0 22px;
  padding: 0;
  list-style: none;
}

.steps__item {
  display: flex;
  align-items: center;
  gap: 7px;
  flex: 1 1 0;
  padding: 9px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-inset);
  color: var(--text-soft);
  font-size: 13.5px;
  transition: color 0.16s ease, border-color 0.16s ease, background 0.16s ease;
}

.steps__item--active {
  color: var(--accent);
  border-color: var(--accent-border);
  background: var(--accent-bg);
}

.steps__dot {
  display: grid;
  place-items: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--bg-soft);
  color: inherit;
  font-size: 12px;
  font-weight: 650;
}

.steps__item--active .steps__dot {
  background: var(--accent);
  color: var(--accent-contrast);
}

.form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.field__row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}

.link-btn {
  border: none;
  background: none;
  padding: 0;
  color: var(--accent);
  font-size: 13px;
  cursor: pointer;
}

.link-btn:disabled {
  color: var(--text-soft);
  cursor: not-allowed;
}

.link-btn:hover:not(:disabled) {
  text-decoration: underline;
}

.actions {
  display: flex;
  gap: 10px;
}

.actions .btn--primary {
  flex: 1 1 auto;
}
</style>
