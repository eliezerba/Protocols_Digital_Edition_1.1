(()=>{
  const EXPECTED='dab9c9d61533cd360bc51e008570e111184ae73c5ddb6aadd3155e1a53c817d4';
  const KEY='protocols-internal-auth-1.1';
  const enc=new TextEncoder();
  const hex=buf=>Array.from(new Uint8Array(buf)).map(b=>b.toString(16).padStart(2,'0')).join('');
  function sha256Fallback(ascii){
    function rr(v,a){return(v>>>a)|(v<<(32-a))}
    const maxWord=Math.pow(2,32),words=[],asciiBitLength=ascii.length*8;
    let hash=sha256Fallback.h=sha256Fallback.h||[],k=sha256Fallback.k=sha256Fallback.k||[],primeCounter=k.length,isComposite={};
    for(let candidate=2;primeCounter<64;candidate++){if(!isComposite[candidate]){for(let i=0;i<313;i+=candidate)isComposite[i]=candidate;hash[primeCounter]=(Math.pow(candidate,.5)*maxWord)|0;k[primeCounter++]=(Math.pow(candidate,1/3)*maxWord)|0}}
    ascii+='\x80';while(ascii.length%64-56)ascii+='\x00';for(let i=0;i<ascii.length;i++){const j=ascii.charCodeAt(i);if(j>>8)return'';words[i>>2]|=j<<((3-i)%4)*8}words[words.length]=((asciiBitLength/maxWord)|0);words[words.length]=asciiBitLength;
    for(let j=0;j<words.length;){const w=words.slice(j,j+=16),oldHash=hash.slice(0);hash=hash.slice(0,8);for(let i=0;i<64;i++){const w15=w[i-15],w2=w[i-2],a=hash[0],e=hash[4];const temp1=hash[7]+(rr(e,6)^rr(e,11)^rr(e,25))+((e&hash[5])^((~e)&hash[6]))+k[i]+(w[i]=(i<16)?w[i]:((w[i-16]+(rr(w15,7)^rr(w15,18)^(w15>>>3))+w[i-7]+(rr(w2,17)^rr(w2,19)^(w2>>>10)))|0));const temp2=(rr(a,2)^rr(a,13)^rr(a,22))+((a&hash[1])^(a&hash[2])^(hash[1]&hash[2]));hash=[(temp1+temp2)|0,hash[0],hash[1],hash[2],(hash[3]+temp1)|0,hash[4],hash[5],hash[6]]}for(let i=0;i<8;i++)hash[i]=(hash[i]+oldHash[i])|0}
    let result='';for(let i=0;i<8;i++)for(let j=3;j+1;j--){const b=(hash[i]>>(j*8))&255;result+=(b<16?'0':'')+b.toString(16)}return result
  }
  async function digest(s){if(globalThis.crypto?.subtle)return hex(await crypto.subtle.digest('SHA-256',enc.encode(s)));return sha256Fallback(s)}
  function unlock(){document.documentElement.classList.remove('locked');document.documentElement.classList.add('unlocked');try{sessionStorage.setItem(KEY,'1')}catch(e){};const p=document.getElementById('passwordInput');if(p)p.value='';}
  function lock(){document.documentElement.classList.add('locked');document.documentElement.classList.remove('unlocked')}
  async function submit(e){e?.preventDefault();const input=document.getElementById('passwordInput'),msg=document.getElementById('passwordMessage');const val=input?.value||'';const ok=await digest(val)===EXPECTED;if(ok){unlock();document.getElementById('authGate')?.setAttribute('aria-hidden','true');document.getElementById('main')?.focus?.()}else{msg.textContent='Incorrect password.';input?.classList.add('auth-error');setTimeout(()=>input?.classList.remove('auth-error'),500);input?.focus()}}
  document.addEventListener('DOMContentLoaded',()=>{let remembered=false;try{remembered=sessionStorage.getItem(KEY)==='1'}catch(e){};if(remembered){unlock();document.getElementById('authGate')?.setAttribute('aria-hidden','true');return}lock();document.getElementById('authForm')?.addEventListener('submit',submit);document.getElementById('passwordInput')?.focus()});
})();
