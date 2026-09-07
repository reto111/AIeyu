const form = document.querySelector('#authForm');
const message = document.querySelector('#authMessage');
const button = document.querySelector('#authSubmit');
const mode = document.body.dataset.authMode;
const params = new URLSearchParams(location.search);
if (mode === 'login' && params.get('registered') === '1') {
  message.textContent = '注册成功，请登录。';
  form.elements.display_name.value = params.get('name') || '';
  history.replaceState(null, '', '/login.html');
}
form.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (button.disabled) return;
  const display_name = form.elements.display_name.value.trim();
  const password = form.elements.password.value.trim();
  if (mode === 'register' && password !== form.elements.confirmation.value.trim()) {
    message.textContent = '两次输入的密码不一致。';
    form.elements.confirmation.focus();
    return;
  }
  button.disabled = true;
  message.textContent = mode === 'register' ? '正在注册...' : '正在登录...';
  try {
    const response = await fetch(`/api/auth/${mode}`, {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({display_name, password}),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || '暂时无法完成，请重试。');
    if (mode === 'register') {
      if (!data.registered || data.authenticated) throw new Error('注册服务版本不匹配，请联系维护者。');
      location.href = `/login.html?registered=1&name=${encodeURIComponent(display_name)}`;
    } else {
      if (!data.authenticated) throw new Error('登录未成功，请重试。');
      location.href = '/';
    }
  } catch (error) {
    message.textContent = error.message;
    button.disabled = false;
  }
});
