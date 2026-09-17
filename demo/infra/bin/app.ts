#!/usr/bin/env node
import "source-map-support/register";
import * as cdk from "aws-cdk-lib";
import { CcfDemoStack } from "../lib/ccf-demo-stack";

const app = new cdk.App();

new CcfDemoStack(app, "CcfDemoStack", {
  description:
    "Curriculum Claim Falsification – hybrid demo (CHAT hackathon 2026)",
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION ?? "us-east-1",
  },
});
