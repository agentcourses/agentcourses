import { deploymentProfile, withBase } from '../../scripts/deployment.mjs';
export const deployment = deploymentProfile(process.env.AC_SITE_MODE);
export const deployed = (path) => withBase(path, deployment.base);
